# -*- coding: utf-8 -*-
import ipaddress

from odoo import models, fields, api, tools, _
import odoo.addons.decimal_precision as dp
from datetime import datetime, timedelta
from odoo.exceptions import Warning, UserError


class CommandeMateriel(models.Model):
    _name = 'commande.materiel'
    _description = 'commande materiel'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'

    def unlink(self):
        for rec in self:
            if rec.state not in ('draft', 'annuler', 'rejeter'):
                raise Warning(
                    _('Vous ne pouvez pas supprimer une demande qui n\'est pas à l\'état de brouillon ou d\'annulation ou de rejet..'))
        return super(CommandeMateriel, self).unlink()

    name = fields.Char('Commande Numéro', copy=False, default="Nouveau", readonly=True)
    date = fields.Date(string='Date',
                       default=fields.Date.today(),
                       required=True, readonly=True)
    employee_id = fields.Many2one('hr.employee', string='Employée',
                                  default=lambda self: self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1),
                                  required=True, copy=True)
    department_id = fields.Many2one('hr.department',
                                    string='Department',
                                    compute='_compute_from_employee_id',
                                    copy=True, )
    employee_confirme_par_id = fields.Many2one('hr.employee',
                                          string='Confirmée par',readonly=True,
                                          copy=False)
    employee_accepter_par_id = fields.Many2one('hr.employee',
                                               string='Acceptée par', readonly=True,
                                               copy=False)
    employee_rejeter_par_id = fields.Many2one('hr.employee',
                                              string='Rejetée par',
                                              readonly=True,
                                              copy=False, )
    employee_aprouver_par_id = fields.Many2one('hr.employee',
                                              string='Approuvée par',
                                              readonly=True,
                                              copy=False, )
    date_confirm = fields.Date(
        string='Date de Confirmation',
        readonly=True,
        copy=False,
    )
    date_accept = fields.Date(
        string='Date d\'Acceptation',
        readonly=True,
        copy=False,
    )
    date_reject = fields.Date(
        string='Date de Rejet',
        readonly=True,
    )
    date_appr = fields.Date(
        string='Date d\'Approbation',
        readonly=True,
        copy=False,
    )
    date_recep = fields.Date(
        string='Date de Réception',
        readonly=True,
        copy=False,
    )
    commande_line_ids = fields.One2many('commande.materiel.line',
                                            'commande_id',
                                            string='Lignes des Commandes',
                                            copy=True,)
    commentaire = fields.Text('Commentaire', required=False)
    motifrejet = fields.Char(string="Motif de Rejet",
                             required=False)
    satisfaction = fields.Selection(string='Satisfaction',
                                    selection=[('non',' '),
                                                ('satisfait', 'Satisfait'),
                                                ('non_satisfait', 'Non Satisfait')],
                                    required=False,
                                    default='non')
    state = fields.Selection([('draft', 'Nouveau'),
                                ('en_cours', 'En Cours Départ.'),
                                ('accepter','Accepté'),
                                ('approuver', 'Approuvé'),
                                ('picking', 'Attendre la Réception'),
                                ('rejeter', 'Rejeté'),
                                ('recu', 'Reçu'),
                                ('annuler', 'Annulé')],
                             default='draft',
                             track_visibility='onchange', )
    picking_count = fields.Integer(compute='compute_pick_count')
    custom_picking_type_id = fields.Many2one('stock.picking.type',
                                             string='Type d\'operation',
                                             default=lambda self: self.env['stock.picking.type'].search([('code','=','internal')], limit=1), copy=False,)
    location_id = fields.Many2one('stock.location', string='Source', copy=True)
    dest_location_id = fields.Many2one('stock.location', string='Destination', required=False, copy=True,)
    delivery_picking_id = fields.Many2one('stock.picking', sring='Transfert Interne',readonly=True, copy=False)
    pick_confirmed = fields.Boolean(compute='get_pick_status', default=False)
    change_commande_line = fields.Boolean('Change liste Commande', compute='allow_edit_line', default=False)

    def _default_value(self):
        return self.env['stock.picking.type'].search([('code','=','internal')], limit=1)


    @api.model
    def create(self, vals):
        name = self.env['ir.sequence'].next_by_code('commande.materiel.seq')
        vals.update({
            'name': name
        })
        res = super(CommandeMateriel, self).create(vals)
        return res

    @api.depends('employee_id')
    def _compute_from_employee_id(self):
        for rec in self:
            if rec.employee_id:
                rec.department_id = rec.employee_id.department_id

    # confirm button
    def confirme_user(self):
        for rec in self:
            rec.employee_confirme_par_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
            rec.date_confirm = fields.Date.today()
            rec.state = 'en_cours'

    def confirme_depart(self):
        for rec in self:
            current_user = rec.env.user
            if rec.env.user.has_group('commande_materiel.group_commande_materiel_daf') or rec.env.user.has_group('commande_materiel.group_commande_materiel_csa') or rec.department_id.manager_id.user_id == current_user:
                rec.date_accept = fields.Date.today()
                rec.employee_accepter_par_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
                rec.state = 'accepter'
            else:
                raise Warning(
                    _('Vous n\'êtes pas autorisé à passer cette action !! Veuillez connecter avec un autre utilisateur'))

    def confirme_manager(self):
        for rec in self:
            current_user = rec.env.user
            if rec.env.user.has_group('commande_materiel.group_commande_materiel_daf') or rec.employee_id.user_id != current_user:
                rec.date_appr = fields.Date.today()
                rec.employee_aprouver_par_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
                rec.state = 'approuver'
            else:
                raise Warning(
                    _('Désolé mais vous ne pouvez pas approuver votre propre demande'))

    def compute_pick_count(self):
        for rec in self:
            order_count = self.env['stock.picking'].search_count([('origin', '=', rec.name)])
            rec.picking_count = order_count

    @api.model
    def _prepare_pick_vals(self, line=False, stock_id=False):
        pick_vals = {
            'product_id': line.product_id.id,
            'product_uom_qty': line.qty,
            'product_uom': line.uom.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.dest_location_id.id,
            'name': line.product_id.name,
            'picking_type_id': self.custom_picking_type_id.id,
            'picking_id': stock_id.id,
            'commande_line_id': line.id,

        }
        return pick_vals

    def request_stock(self):
        stock_obj = self.env['stock.picking']
        move_obj = self.env['stock.move']
        for rec in self:
            if not rec.commande_line_ids:
                raise Warning(_('Veuillez créer votre ligne de demande,'))
            if not rec.location_id:
                raise Warning(_('Veuillez sélectionneer l\'emplacement source'))
            if not rec.custom_picking_type_id.id:
                raise Warning(_('Veuillez sélectionneer le type d\'opération.'))
            if not rec.dest_location_id:
                raise Warning(_('Veuillez sélectionneer l\'emplacement de destination'))
            picking_valus = {
                'partner_id' : rec.employee_id.sudo().address_home_id.id,
                #'min_date' : fields.Date.today(),
                'location_id' : rec.location_id.id,
                'location_dest_id' : rec.dest_location_id and rec.dest_location_id.id or rec.employee_id.dest_location_id.id or rec.employee_id.department_id.dest_location_id.id,
                'picking_type_id' : rec.custom_picking_type_id.id,#internal_obj.id,
                'note' : rec.commentaire,
                'commande_id' : rec.id,
                'origin' : rec.name,

            }
            stock_id = stock_obj.sudo().create(picking_valus)
            livraison_vals = {
                'delivery_picking_id' : stock_id.id,
            }
            rec.write(livraison_vals)
        for line in rec.commande_line_ids:
            pick_vals = rec._prepare_pick_vals(line, stock_id)
            move_id = move_obj.sudo().create(pick_vals)
            rec.state = 'picking'

    def recu_user(self):
        for rec in self:
            user = rec.env.user
            emplyer = rec.employee_id.user_id
            departement_manger = rec.department_id.manager_id.user_id
            if emplyer == user or departement_manger == user:
                if rec.satisfaction == 'non':
                    raise Warning(
                                 _('Veuillez selectionner votre niveau de satisfaction !!'))
                rec.date_recep = fields.Date.today()
                rec.state = 'recu'
            else:
                raise Warning(
                    _('Vous n\'êtes pas autorisé de passer cette action !!'))


    def reject_commande(self):
        for rec in self:
            if rec.motifrejet == False:
                raise Warning(
                    _('Le champ Motif de Rejet ne doit pas être vide !!'))
            else:
                rec.date_reject = fields.Date.today()
                rec.employee_rejeter_par_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
                rec.state = 'rejeter'

    def annulee_commande(self):
        for rec in self:
            rec.state = 'annuler'

    def show_picking(self):
        for rec in self:
            res = self.env.ref('stock.action_picking_tree_all').sudo()
            res = res.read()[0]
            res['domain'] = str([('commande_id','=', rec.id)])
            res['context'] = "{'create': False}"
        return res

    def get_pick_status(self):
        for rec in self:
            commande_pick = rec.env['stock.picking'].search([('origin', '=', rec.name)])
            comm_pick_state = commande_pick.filtered(lambda r : r.state == 'done')
            if rec.state == 'picking':
                if len(commande_pick) >= 1:
                    if len(commande_pick) == len(comm_pick_state):
                        rec.pick_confirmed = True
                    else:
                        rec.pick_confirmed = False
                else:
                    rec.pick_confirmed = False
            else:
                rec.pick_confirmed = False

    def allow_edit_line(self):
        for rec in self:
            if rec.state == 'draft':
                rec.change_commande_line = True
            elif rec.state == 'accepter':
                if (rec.env.user.has_group('commande_materiel.group_commande_materiel_csa') or rec.env.user.has_group('commande_materiel.group_commande_materiel_daf')) and rec.state == 'accepter':
                    rec.change_commande_line = True
                else:
                    rec.change_commande_line = False
            elif rec.state == 'approuver':
                if (rec.env.user.has_group('commande_materiel.group_commande_materiel_csa') or rec.env.user.has_group('commande_materiel.group_commande_materiel_daf')) and rec.state == 'approuver':
                    rec.change_commande_line = True
                else:
                    rec.change_commande_line = False
            else:
                rec.change_commande_line = False


class CommandeMaterielLine(models.Model):
    _name = "commande.materiel.line"
    _description = 'Commande Materie Lines'

    commande_id = fields.Many2one('commande.materiel', string='Commande',)
    product_id = fields.Many2one('product.product', string='Product',)
    description = fields.Char(string='Description', required=True,)
    qty = fields.Float(string='Quantity', default=1, required=True,)
    uom = fields.Many2one('uom.uom', string='Unit of Measure', required=True,)
    commande_picking = fields.Boolean(string='Commande type',  required=False, default=True)

    commande_type = fields.Selection(selection=[('internal', 'Internal Picking'),
                                                ('purchase', 'Purchase Order'),],
                                                string='Requisition Action',)

    @api.onchange('product_id')
    def onchange_product_id(self):
        for rec in self:
            if rec.product_id:
                rec.description = rec.product_id.name
                rec.uom = rec.product_id.uom_id.id
