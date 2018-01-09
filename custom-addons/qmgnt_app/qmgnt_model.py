# -*- coding: utf-8 -*-


from odoo import models, fields, tools, api, _


class productTask(models.Model):
    _name = 'productdata'
    _description = 'Product Data'
    _rec_name = 'product_name'
    id=fields.Integer()
    product_name = fields.Many2one('product.product')
    norm = fields.Float('Norm')
    norm_unit = fields.Char('Norm_unit', default='mm')
    tolerance_min = fields.Float('Tolerance_min')
    tolerance_max = fields.Float()
    test_type = fields.Selection([('one', 'Pass- Fail'), ('two', 'Measure'),
                                  ('three', 'Dummy'), ('four', 'Take a Picture')], 'State', default='one')



class operationTask(models.Model):
    _name = 'operation'
    _description = 'Operations'
    _rec_name = 'operation_name'
    operation_name = fields.Char('Operation')



class teamTask(models.Model):
    _name = 'quality_alert_team'
    _description = 'Quality alert team'
    _rec_name = 'team_name'
    team_name = fields.Char('Team name')

    email = fields.Char('Email')

    @api.one
    @api.depends('team_name')
    def _get_count(self):
        for team in self.team_name:
            name = self.env.context.get('default_product_id', self.team_name)
            alert_count = self.env['quality_alert'].search(
                [('team_id', '=', name)])
            check_count = self.env['quality_check'].search(
                [('status', '!=', 'open'), ('status', '!=', 'done'), ('team_name', '=', name)])
            self.alert_count = len(alert_count)
            self.check_count = len(check_count)
        print name

    color = fields.Integer(string='Color Index')
    name = fields.Char(string="Name")
    alert_count = fields.Integer(compute='_get_count')
    check_count = fields.Integer(compute='_get_count')


class controlTask(models.Model):
    _name = 'quality.product'
    _description = 'Quality Management'
    _rec_name = 'sequence_id'
    sequence_id = fields.Char('Reference', index=True,copy=False, readonly=True, default=lambda x: _('New'))
    title = fields.Char('Title',required='True')
    product_name = fields.Many2one('productdata', 'Product',required='True')
    #picking_type_id = fields.Integer('Picking_type_id')
    operation_name = fields.Many2one('operation', 'Operation')
    person_name = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)

    control_type = fields.Selection([('one', 'All Operations'), ('two', 'Randomly'),
                                     ('three', 'Periodically')], 'Control Type', default='one')

    test_type = fields.Selection([('one', 'Pass- Fail'), ('two', 'Measure'),
                                  ('three', 'Dummy'), ('four', 'Take a Picture')],related='product_name.test_type')
    team_name = fields.Many2one('quality_alert_team', 'Team',required='True')
    user_id = fields.Integer('User_id')
    notes = fields.Text('Notes')
    instruction = fields.Text('Instructions')
    reason = fields.Text('Reason')
    message = fields.Text('Message If Failure')
    measure_frequency_unit_value = fields.Integer('measure_frequency_unit_value')
    measure_frequency_unit = fields.Selection([('one', 'Days'), ('two', 'Weeks'),
                                               ('three', 'Months')], 'Frequency Unit', default='one')
    norm = fields.Float('Norm',related='product_name.norm')
    norm_unit = fields.Char('Norm_unit', default='mm',related='product_name.norm_unit')
    tolerance_min = fields.Float('Tolerance_min',related='product_name.tolerance_min')
    check = fields.Boolean('Checked?')
    tolerance_max = fields.Float(related='product_name.tolerance_max')

    @api.model
    def create(self, values):

        if values.get('sequence_id', _('New')) == _('New'):
            values['sequence_id'] = self.env['ir.sequence'].next_by_code('bharpai.bharpai') or _('New')

        return super(controlTask, self).create(values)


    @api.multi
    def open_second_class(self):
        self.ensure_one()
        res = self.env['ir.actions.act_window'].for_xml_id('qmgnt_app', 'action_todo_task01')
        res.update(
            context=dict(self.env.context, default_point_id=self.id, search_default_parent_false=True),
            domain=[('point_id', '=', self.sequence_id)]

        )
        return res



class qcheckTask(models.Model):
    _name = 'quality_check'
    _description = 'Quality Check'
    _rec_name = 'sequence_id'

    sequence_id = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'))
    team_name = fields.Many2one('quality_alert_team', 'Team', required='True',related="point_id.team_name")
    product_name = fields.Many2one('productdata', 'Product', required='True',related="point_id.product_name")
    operation = fields.Selection([('draft', 'New'), ('open', 'Started'),
                                  ('done', 'Closed')], String="Operation")
    notes = fields.Text('Notes',related="point_id.notes")
    point_id = fields.Many2one('quality.product',String='Check')
    product_id = fields.Many2one('quality.product', 'Product')
    status = fields.Selection([('draft', 'Todo'), ('open', 'passed'),
                               ('done', 'Failed')], 'Status', default='draft')
    check_date = fields.Datetime('Date From', required=True, default=fields.Datetime.now)
    check_by = fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)

    measure=fields.Float('Measure')

    test_type = fields.Selection([('one', 'Pass- Fail'), ('two', 'Measure'),
                                  ('three', 'Dummy'), ('four', 'Take a Picture')],related='point_id.test_type', default='one')
    @api.model
    def create(self, values):
        if values.get('sequence_id', _('New')) == _('New'):
            values['sequence_id'] = self.env['ir.sequence'].next_by_code('bharpai.bharpai1') or _('New')
        return super(qcheckTask, self).create(values)

    @api.one
    def do_Pass(self):
        for task in self:
            task.write({'status': 'open'})
            return True



    @api.one
    def open_class(self):
        #view = self.env.ref('qmgnt_app.view_form_todo_task1')
        self.ensure_one()

        slip = self.env['quality_alert'].create({
                'Check': self.id,
                'team_id': self.team_name.id,

                'product_name': self.product_name.id

            })
        slip.write({'stage': 'one'})
        return slip


    @api.one
    def do_Fail(self):
        self.write({'status': 'done'})
        # obj = self._context.get('point_id')
        # print  obj
        # obj1= obj.context.get('point_id')
        # print obj1


class tagTask(models.Model):
    _name = 'quality_tag'
    _description = 'Quality Tag'
    tag_ids = fields.Integer('Tag Ids')
    name = fields.Char('Tag name')




class reasonTask(models.Model):
    _name = 'quality_reason'
    _description = 'Quality Reason'
    reason_id = fields.Integer('Reason Id')
    name = fields.Char('reason name')


class alertTask(models.Model):
    _name = 'quality_alert'
    _description = 'Quality Alert'
    _rec_name = 'sequence_id'
    sequence_id = fields.Char('Reference', copy=False, readonly=True, default=lambda x: _('New'))

    description = fields.Text('Description')
    action_corrective = fields.Text('Action_corrective')
    action_preventive = fields.Text('Action_preventive')
    #partner_id = fields.Char('Partner_id')
    date_assign = fields.Datetime('Date From', default=fields.Datetime.now)
    stage = fields.Selection([('one', 'New'), ('two', 'Confirmed'),('three', 'Action Proposed'),
                                  ('four', 'Solved')], String="Stage",default='one')
    quality_check = fields.Boolean('Quality Check', default=False)
    person_name =  fields.Many2one('res.users', 'Responsible', default=lambda self: self.env.user)

    Check = fields.Many2one('quality_check', String="Check")
    priority = fields.Selection(
        [('0', 'Low'), ('1', 'Normal'), ('2', 'Medium'), ('3', 'High')],
        'Priority')
    reason_id = fields.Many2one('quality_reason', 'reason_id')
    tag_ids = fields.Many2one('quality_tag', 'tag_ids')
    # user_id=fields.Integer('User Id')
    team_id = fields.Many2one('quality_alert_team')
    product_name = fields.Many2one('productdata', 'Product')

    @api.model
    def create(self, values):
        if values.get('sequence_id', _('New')) == _('New'):
            values['sequence_id'] = self.env['ir.sequence'].next_by_code('bharpai.bharpai2') or _('New')

        return super(alertTask, self).create(values)

    @api.one
    def do_confirm(self):
        self.write({'stage': 'two'})



    @api.one
    def do_action(self):
        self.write({'stage': 'three'})

    @api.one
    def do_finish(self):
        self.write({'stage': 'four'})
