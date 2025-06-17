from odoo import models, fields, api



class Partner(models.Model):
    _inherit = "res.partner"
    _description = "Res Partner"

    # date = fields.Date('Partner since', help="Date of activation of the partner or patient")
    # ref = fields.Char('ID Number')
    # is_person = fields.Boolean('Person', help="Check if the partner is a person.")
    # is_manager = fields.Boolean('manger', help="Check if the partner is a doctor")
    # is_institution = fields.Boolean('Institution', help="Check if the partner is a Medical Center")
   

    
  
    name_ar = fields.Char(string="Arabic Full Name", required=True)
    firstname = fields.Char("First Name", size=128, help="Last Name")
    lastname = fields.Char('Last Name', size=128, help="Last Name")
    
    last_renewal_date = fields.Date(store=True)
    # last_renewal_date = fields.Date(compute="_compute_last_renewal_date", store=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('approved', 'Approved'),
        ('black_list', 'Blacklisted'),
    ], default='draft')
    # branch_ids = fields.Many2many('res.branch', string="Branches")

    # @api.depends('name')
    # def _compute_last_renewal_date(self):
    #     for rec in self:
    #         order = self.env['sale.order'].search([
    #             ('partner_id', '=', rec.id),
    #             ('quotation_template_id.name', '=', 'Renewal')
    #         ], order='date_order desc', limit=1)
    #         rec.last_renewal_date = order.date_order if order else False
   
    
    
    # @api.depends('name', 'lastname')
    # def name_get(self):
    #     result = []
    #     for partner in self:
    #         name = partner.name
    #         if partner.lastname:
    #             name += ' ' + partner.lastname
    #         if partner.lastname:
    #             name = partner.lastname + ', ' + name
    #         result.append((partner.id, name))
    #     return result   