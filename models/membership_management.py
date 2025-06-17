from odoo import _, models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError
import logging
from collections import defaultdict

_logger = logging.getLogger(__name__)

class MemberShipManagement(models.Model):
    _name = 'membership.management.club'
    _description = 'Membership Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # مهم جداً
    # _order = 'last_renewal_date desc'

    name = fields.Char('Reference', required=True, copy=False, readonly=True, default='New')
    #  default=lambda self: _('New')
    partner_id = fields.Many2one(
        'res.partner',
        string='Member',
        domain="[('membership_state', 'in', ['invoiced', 'paid', 'free'])]",
        required=True,
        ondelete='cascade',
        index=True,
        track_visibility='onchange'
    )
    company_id = fields.Many2one(
            'res.company',
            string='Company',
            related='partner_id.company_id',
             store=True,
    readonly=True
            # default=lambda self: self.env.company
        )

    membership_product_id = fields.Many2one('product.product', string='Membership Product',
                                             domain="[('product_tmpl_id.membership', '=', True)]",  tracking=True)
    
    membership_date_from = fields.Date(
        string='Membership Start Date',
        help='Date from which membership becomes active.'
    )
    membership_date_to = fields.Date(
        string='Membership End Date',
        help='Date until which membership remains active.'
    )
    last_renewal_date = fields.Date(
        compute='_compute_last_renewal_date',
        store=True,
        string='Last Renewal Date'
    )

    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('black_list', 'Blacklisted'),
    ], default='draft', string="Status", tracking=True)

    active = fields.Boolean('Active', default=True)
    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('membership.management.club') or 'New'
        return super(MemberShipManagement, self).create(vals)
   

  


    @api.onchange('membership_product_id')
    def _onchange_membership_product_id(self):
        for rec in self:
            product = rec.membership_product_id.product_tmpl_id
            if product and product.membership:
                rec.membership_date_from = product.membership_date_from
                rec.membership_date_to = product.membership_date_to
            else:
                rec.membership_date_from = False
                rec.membership_date_to = False

    def set_to_approved(self):
        self.ensure_one()
        self.status = 'approved'
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': 'Created %s membership for member %s' % (self.name, self.partner_id.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def set_to_blacklist(self):
        self.ensure_one()
        self.status = 'black_list'

    def set_to_draft(self):
        self.ensure_one()
        self.status = 'draft'
        
    def create_renewal_order(self):
        """Create a sale order for membership renewal"""
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Please select a member first!"))
            
        if not self.membership_product_id:
            raise UserError(_("Please select a membership product first!"))
        
        # Check if membership is expired or about to expire
        if not self.is_expired and self.days_until_expiry > 30:
            raise UserError(_("Membership is still valid for %s days!") % self.days_until_expiry)
        
        # Create sale order
        order_vals = {
            'partner_id': self.partner_id.id,
            'validity_date': fields.Date.add(fields.Date.today(), days=30),
            'order_line': [(0, 0, {
                'product_id': self.membership_product_id.id,
                'product_uom_qty': 1,
                'price_unit': self.membership_product_id.list_price,
                'tax_id': [(6, 0, self.membership_product_id.taxes_id.ids)]
            })]
        }
        
        sale_order = self.env['sale.order'].create(order_vals)
        
        # Return action to open the created order
        return {
            'name': _('Sale Order'),
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order',
            'res_id': sale_order.id,
            'view_mode': 'form',
            'target': 'current',
        }
        
    @api.depends('partner_id')
    def _compute_last_renewal_date(self):
        '''Compute the last renewal date for each membership
        Enhance your _compute_last_renewal_date method to properly track renewals'''
        for rec in self:
            if not rec.partner_id:
                rec.last_renewal_date = False
                continue
                
            # Find the most recent confirmed sale order for this membership
            sale_order = self.env['sale.order'].search([
                ('partner_id', '=', rec.partner_id.id),
                ('state', 'in', ['sale', 'done']),
                ('order_line.product_id', '=', rec.membership_product_id.id)
            ], order='date_order desc', limit=1)
            
            rec.last_renewal_date = sale_order.date_order if sale_order else False
            # Move the print statement inside the for loop
            print("rec.last_renewal_date is %s and sale_order is %s" % (rec.last_renewal_date, sale_order))    
    renewal_order_ids = fields.One2many(
        'sale.order',
        compute='_compute_renewal_orders',
        string='Renewal Orders'
    )

    renewal_order_count = fields.Integer(
        compute='_compute_renewal_orders',
        string='Renewal Count'
    )

    # def _compute_renewal_orders(self):
    #     for rec in self:
    #         orders = self.env['sale.order'].search([
    #             ('partner_id', '=', rec.partner_id.id),
    #             ('order_line.product_id', '=', rec.membership_product_id.id)
    #         ])
    #         rec.renewal_order_ids = orders
    #         rec.renewal_order_count = len(orders)

    # def action_view_renewal_orders(self):
    #     self.ensure_one()
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Renewal Orders',
    #         'res_model': 'sale.order',
    #         'view_mode': 'tree,form',
    #         'domain': [('id', 'in', self.renewal_order_ids.ids)],
    #         'context': {'create': False},
    #     }
        
    @api.constrains('membership_product_id')
    def _check_membership_product(self):
        for rec in self:
            if rec.membership_product_id and not rec.membership_product_id.membership:
                raise ValidationError(_("The selected product must be a membership product!"))
    
    
    is_expired = fields.Boolean(
        string='Expired',
        compute='_compute_membership_status',
        store=True,
        help='True if membership has expired'
    )
    days_until_expiry = fields.Integer(
        string='Days Until Expiry',
        compute='_compute_membership_status',
        store=True,
        help='Number of days until membership expires'
    )

    membership_state = fields.Selection(
        related='partner_id.membership_state',
        string='Membership State',
        store=True
        )
    @api.depends('membership_date_to', 'status', 'membership_date_from')
    def _compute_membership_status(self):
        today = fields.Date.today()
        for rec in self:
            rec.is_expired = False
            rec.days_until_expiry = 0
            
            if rec.membership_date_to and rec.status == 'approved':
                delta = (rec.membership_date_to - today).days
                rec.is_expired = delta < 0
                rec.days_until_expiry = max(0, delta)
            elif not rec.membership_date_to:
                # إذا لم يكن هناك تاريخ انتهاء، اعتبر أن العضوية غير منتهية الصلاحية
                rec.is_expired = False
                rec.days_until_expiry = 0  # أو أي قيمة افتراضية تريدها
                
    
    @api.model
    def _cron_check_expired_memberships(self):
        """Daily check for expired memberships"""
        try:
            today = fields.Date.today()
            expired_memberships = self.search([
                ('membership_date_to', '<', today),
                ('status', '=', 'approved'),
                ('is_expired', '=', True)
            ])
            print('expired_memberships', expired_memberships)
            
            if expired_memberships:
                # Mark as expired
                expired_memberships.write({'is_expired': True})
                
                # Send notification email
                template = self.env.ref('membership_management_kode.email_template_expired_membership', raise_if_not_found=False)
                if template:
                    for membership in expired_memberships:
                        # Add context or custom values if needed
                        template.with_context(
                            member_name=membership.partner_id.name,
                            expiry_date=membership.membership_date_to
                        ).send_mail(membership.id, force_send=True)
                        print('email sent')
                else:
                    _logger.warning("Email template 'email_template_expired_membership' not found")
        except Exception as e:
         _logger.error("Failed to check expired memberships: %s", str(e)) 
                
                
    sale_order_count = fields.Integer(
        compute='_compute_sale_order_count',
        string='Sale Orders'
    )
    
    @api.depends('partner_id', 'membership_product_id')
    def _compute_sale_order_count(self):
        for rec in self:
            if rec.partner_id and rec.membership_product_id:
                rec.sale_order_count = self.env['sale.order'].search_count([
                    ('partner_id', '=', rec.partner_id.id),
                    ('order_line.product_id', '=', rec.membership_product_id.id)
                ])
            else:
                rec.sale_order_count = 0
    def action_view_sale_orders(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale Orders',
            'res_model': 'sale.order',
            'view_mode': 'tree,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('order_line.product_id', '=', self.membership_product_id.id)
            ],
            'context': {'create': False}
        }
        
        
    join_date = fields.Date(
        string='Join Date',
        default=fields.Date.today(),
        help='Date when the member joined the club'
    )
    
    membership_fee = fields.Float(
        string='Membership Fee',
        related='membership_product_id.list_price',
        store=True,
        help='Current membership fee'
    )
       # Add this field to your existing model
    member_lines = fields.One2many(
        'membership.membership_line',
        compute='_compute_member_lines',
        string='Membership History'
    )
    
    @api.depends('partner_id')
    def _compute_member_lines(self):
        for rec in self:
            rec.member_lines = self.env['membership.membership_line'].search([
                ('partner', '=', rec.partner_id.id)
            ])
    
    
  