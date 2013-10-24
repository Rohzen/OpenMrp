##############################################################################
#
#    Parametric Products, version 2.0
#    Compatible with OpenERP release 7.0.0
#    Copyright (C) 2013 Roberto Zanardo. All Rights Reserved.
#    Email: info@progressive.it
#    Based on Parametric Products, version 1.0
#    Compatible with OpenERP release 5.0.0
#    Copyright (C) 2009 Andrea Polla. All Rights Reserved.

#    Web site: http://sites.google.com/site/opensourceerp
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from osv import fields, osv
import netsvc
import time
import pooler
import math
from mx import DateTime
import openerp.addons.decimal_precision as dp
from openerp.osv import fields, osv

glob_orderid = 0
glob_bom_id = 0
#-----------------------------------------------------------------------------
# module: product
#-----------------------------------------------------------------------------

# Create a new object to represent the parameters.

class product_parameter(osv.osv):
    _name = "product.parameter"
    _description = "Product Parameters"
    _columns = {
        'name': fields.char('Parameter', size=64, required=True),
        'description': fields.char('Description', size=64, required=True),
        'uom_id': fields.many2one('product.uom', 'Unit of Measure', required=True),
        'default': fields.float('Default Value', digits=(16,2), required=True),
        'comment': fields.text('Comment description'),
    }
    _defaults = {
        'default': lambda *a: 0.0,
    }
    _sql_constraints = [
        ('name_uniq', 'unique (name)', 'The parameter name must be unique.')
    ]
product_parameter()

# Add a new product field to associate parameters to products.

class product_product(osv.osv):
    _inherit = "product.product"
    _columns = {
        'parameters_ids': fields.many2many('product.parameter',
            'product_parameter_rel',
            'prod_id',
            'parameter_id',
            'Parameters'),
    }
product_product()

#-----------------------------------------------------------------------------
# module: mrp
#-----------------------------------------------------------------------------

# Create the object containing the formulas associated to the bom.

class mrp_bom_parameter(osv.osv):
    _name = 'mrp.bom.parameter'
    _description = 'Parameters Values'
    _columns = {
        'parameter_id': fields.many2one('product.parameter', 'Name'),
        'value': fields.char('Formula', size=128),
        'bom_id': fields.many2one('mrp.bom', 'BoM'),
        'eval_order': fields.integer('eval_order', help="ordine di valutazione delle formule"),
    }
mrp_bom_parameter()

# Add a new field to the bill of materials which will contain the parameter values (formulas) references.
# Add a new method _bom_compute_parameters to evaluate the formulas in a given bom.

class mrp_bom(osv.osv):
    _inherit = "mrp.bom"
    _columns = {
        'parameter_ids': fields.one2many('mrp.bom.parameter', 'bom_id', 'Parameters Values'),
    }
    
    def _bom_compute_parameters(self, cr, uid, bom, sale_order_line_id, properties, addthis=False, level=10):
        ##debug roberto
        ##print '-----------------\n'
        ##print '_bom_compute_parameters(run one for each parameter)\n'
        ##print '-----------------\n'
        
        ##taked from wizard: get parameters
##        pool = pooler.get_pool(cr.dbname)
##        bom = pool.get('mrp.bom').browse(cr, uid, data['ids'])[0]
##        # res is used to specify an initial value for each field
##        res = {}
##        fields.clear()
##        # begin the dynamic construction of the form
##        index = 0
##        # for each product with parameters, add the product name and each of its parameters to the form
##        for line in bom.bom_lines:
##            param_ids = line.product_id.parameters_ids
##            if param_ids:
##                # add product name as a separator
##                for param_id in line.product_id.parameters_ids:
##                    # initial value comes from bom line (formula previously set) or from the default value in product
##                    paramline_id = pool.get('mrp.bom.parameter').search(cr, uid, [('bom_id','=',line.id),('parameter_id','=',param_id.id)])
##                    if paramline_id:
##                        val = pool.get('mrp.bom.parameter').read(cr, uid, paramline_id, ['value'])
##                        v = val[0]['value'] or ''
##                    else:
##                        v = param_id.default or ''
##                    # set initial value for this field
##                    res['param%s' % index] = v
##                    index += 1
##
##        ##taked from wizard: confirm values
##        pool = pooler.get_pool(cr.dbname)
##        bom = pool.get('mrp.bom').browse(cr, uid, data['ids'])[0]
##        index = 0
##        # update the parameters value for each bom component
##        for line in bom.bom_lines:
##            param_ids = line.product_id.parameters_ids
##            if param_ids:
##                # delete previously inserted parameter values
##                paramline_ids = pool.get('mrp.bom.parameter').search(cr, uid, [('bom_id','=',line.id)])
##                if paramline_ids:
##                    pool.get('mrp.bom.parameter').unlink(cr, uid, paramline_ids)
##                # insert current parameter values
##                for param_id in line.product_id.parameters_ids:
##                    pool.get('mrp.bom.parameter').create(cr, uid, {
##                        'parameter_id': param_id.id,
##                        'value': data['form']['param%s' % index],
##                        'bom_id': line.id
##                    })
##                    index += 1

        
        # fine debug roberto
        if bom.type=='phantom' and not bom.bom_lines:
            newbom = self._bom_find(cr, uid, bom.product_id.id, bom.product_uom.id, properties)
            if newbom:
                res = self._bom_compute_parameters(cr, uid, self.browse(cr, uid, [newbom])[0], sale_order_line_id, properties, addthis=True, level=level+10)
        else:
            if (addthis and not bom.bom_lines) or (level > 10 and bom.bom_lines):
                # retrieve the parameters already evaluated
                parameters_ids = self.pool.get('mrp.parameters').search(cr, uid, [('sale_line_id','=',sale_order_line_id)])
                parameters = self.pool.get('mrp.parameters').browse(cr, uid, parameters_ids)

               # build the namespace used to evaluate the formulas
                formula_namespace = {}
                for p in parameters:
                    formula_namespace[p.name] = p.value
                    ##print '-----------------\n'
                    #print '_bom_compute_formula(run one for each parameter)\n %s - %s' % (p.name,p.value)
                    ##print '-----------------\n'

                #print 'bom.product_id:%s' % bom.product_id
                param_ids = bom.product_id.parameters_ids
                if param_ids:
                    for param_id in bom.product_id.parameters_ids:
                        #open("D:\compute.txt","a").write('search param_ids:%s in mrp.bom.parameter \nfor bom.id:%s param_id.id:%s bom.bom_id:%s\n' % (param_ids,bom.id,param_id.id,bom.bom_id))
                        #print 'search param_ids:%s in mrp.bom.parameter for bom.id:%s param_id.id:%s bom.bom_id:%s' % (param_ids,bom.id,param_id.id,bom.bom_id)
                        # initial value comes from bom line (formula previously set) or from the default value in product
                        paramline_id = self.pool.get('mrp.bom.parameter').search(cr, uid, [('bom_id','=',glob_bom_id),('parameter_id','=',param_id.id)])
                        if paramline_id:
                            #open("c:\temp\compute.txt","a").write('paramline_id:%s\n' % (paramline_id))
                            val = self.pool.get('mrp.bom.parameter').read(cr, uid, paramline_id, ['value'])
                            p_id = self.pool.get('product.parameter').search(cr, uid, [('id','=',param_id.id)])
                            name = self.pool.get('product.parameter').read(cr, uid, p_id, ['name'])
                            pname = name[0]['name'] or ''
                            v = val[0]['value'] or ''
                            print 'v1:%s' % v
                            ##evaluate the formula; use a try statement to protect against possible errors in the formula
                            try:
                            ##print '-----------------\n'
                            ##    print '_bom_compute new_formula paramline_id.value:%s - formula_namespace:%s' % (v,formula_namespace)
                            ##print '-----------------\n'  
                                parameter_value = eval(v, formula_namespace)
                                print 'Param Name:%s Result:%s' % (pname,parameter_value)
                            except:
                                raise osv.except_osv('Invalid Formula','The formula "%s" (parameter "%s") cannot be evaluated.' % (v,pname))
                            # update formula namespace (necessary if a parameter depends on other parameters of the same product)
                            formula_namespace[pname] = parameter_value
                            # save parameter value (may be needed later to evaluate other formulas)
                            self.pool.get('mrp.parameters').create(cr, uid, {
                                'name': pname,
                                'value': parameter_value,
                                'sale_line_id': sale_order_line_id,
                            })
                        else:
                            v = param_id.default or ''
                            print 'v2:%s' % v
                        # set initial value for this field
                        #res['param%s' % index] = v
                        #index += 1
                        
                #bparameters_ids = self.pool.get('mrp.bom.parameter').search(cr, uid, [('bom_id','=',bom.bom_id)])
                #bparameters = self.pool.get('mrp.bom.parameter').browse(cr, uid, bparameters_ids)
                
##                for p_id in bom.parameters_ids:
##                    # evaluate the formula; use a try statement to protect against possible errors in the formula
##                    try:
##                    ##print '-----------------\n'
##                        print '_bom_compute new_formula(run one for each parameter) %s - %s' % (p_id.value,formula_namespace)
##                    ##print '-----------------\n'  
##                        parameter_value = eval(p_id.value, formula_namespace)
##                    except:
##                        raise osv.except_osv('Invalid Formula','The formula "%s" (parameter "%s") cannot be evaluated.' % (p_id.value, p_id.parameter_id.name))
##                    # update formula namespace (necessary if a parameter depends on other parameters of the same product)
##                    formula_namespace[p_id.parameter_id.name] = parameter_value
##                    # save parameter value (may be needed later to evaluate other formulas)
##                    self.pool.get('mrp.parameters').create(cr, uid, {
##                        'name': p_id.parameter_id.name,
##                        'value': parameter_value,
##                        'sale_line_id': sale_order_line_id,
##                    })
            for bom2 in bom.bom_lines:
                res = self._bom_compute_parameters(cr, uid, bom2, sale_order_line_id, properties, addthis=True, level=level+10)
            
mrp_bom()

# Create a new object which will hold the value of the parameters associated to the product in a
# given sale order line and of all its components.

class mrp_parameters(osv.osv):
    _name = 'mrp.parameters'
    _description = 'Production Parameters Values'
    _columns = {
        'name': fields.char('Value', size=64, readonly=True),
        'value': fields.float('Value', digits=(16,2), required=True),
        'sale_line_id': fields.integer('Order Line'),
    }
mrp_parameters()

# Add a field to the procurement orders which will be used to relate a procurement order and the
# sale order line which originated it.
# Modify the action_produce_assign_product method to insert the sale order line id in the
# production order which is created.

class procurement_order(osv.osv):
    _inherit = 'procurement.order'
    _columns = {
        'order_line_id': fields.integer('Order Line'),
    }

    def action_produce_assign_product(self, cr, uid, ids, context={}):
        ## debug roberto
        print '-----------------\n'
        print 'action_produce_assign_product (procurement)\n'
        print '-----------------\n'
        ## fine debug roberto
        produce_id = False
        company = self.pool.get('res.users').browse(cr, uid, uid, context).company_id
        for procurement in self.browse(cr, uid, ids):
            res_id = procurement.move_id.id
            loc_id = procurement.location_id.id
            newdate = DateTime.strptime(procurement.date_planned, '%Y-%m-%d %H:%M:%S') - DateTime.RelativeDateTime(days=procurement.product_id.product_tmpl_id.produce_delay or 0.0)
            newdate = newdate - DateTime.RelativeDateTime(days=company.manufacturing_lead)
            produce_id = self.pool.get('mrp.production').create(cr, uid, {
                'origin': procurement.origin,
                'product_id': procurement.product_id.id,
                'product_qty': procurement.product_qty,
                'product_uom': procurement.product_uom.id,
                'product_uos_qty': procurement.product_uos and procurement.product_uos_qty or False,
                'product_uos': procurement.product_uos and procurement.product_uos.id or False,
                'location_src_id': procurement.location_id.id,
                'location_dest_id': procurement.location_id.id,
                'bom_id': procurement.bom_id and procurement.bom_id.id or False,
                'date_planned': newdate.strftime('%Y-%m-%d %H:%M:%S'),
                'move_prod_id': res_id,
                'order_line_id': procurement.order_line_id,
            })
            ##debug roberto
            print '-----------------\n'
            print 'action_produce_assign_product\n - bom:%s' %  procurement.bom_id
            print '-----------------\n'
            ## fine debug roberto
            self.write(cr, uid, [procurement.id], {'state':'running'})
            bom_result = self.pool.get('mrp.production').action_compute(cr, uid,
                    [produce_id], properties=[x.id for x in procurement.property_ids])
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'mrp.production', produce_id, 'button_confirm', cr)
        return produce_id
procurement_order()

def rounding(f, r):
    if not r:
        return f
    return round(f / r) * r

# Add a field to the production orders which will contain the sale order line id that comes from the
# procurement order.
# Modify the action_compute method in order to evaluate the formulas: just after the _bom_explode call,
# add a call to the new method _bom_compute_parameters.
# Modify the action_confirm method in such a way that, if a procurement order is created, the
# sale order sale id will be saved in that procurement order.

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'order_line_id': fields.integer('Order Line')
    }

    def action_compute(self, cr, uid, ids, properties=[],context={}):
        ## debug roberto
        print '-----------------\n'
        print 'action_compute(mrp production)\n'
        print '-----------------\n'
        ## fine debug roberto
        results = []
        for production in self.browse(cr, uid, ids):
            cr.execute('delete from mrp_production_product_line where production_id=%s', (production.id,))
            cr.execute('delete from mrp_production_workcenter_line where production_id=%s', (production.id,))
            bom_point = production.bom_id
            bom_id = production.bom_id.id
            if not bom_point:
                bom_id = self.pool.get('mrp.bom')._bom_find(cr, uid, production.product_id.id, production.product_uom.id, properties)
                if bom_id:
                    bom_point = self.pool.get('mrp.bom').browse(cr, uid, bom_id)
                    routing_id = bom_point.routing_id.id or False
                    self.write(cr, uid, [production.id], {'bom_id': bom_id, 'routing_id': routing_id})

            if not bom_id:
                raise osv.except_osv('Error', "Couldn't find bill of material for product")

            print 'bom_id: %s' %  (bom_id)
            global glob_bom_id
            glob_bom_id = bom_id
            #if bom_point.routing_id and bom_point.routing_id.location_id:
            #   self.write(cr, uid, [production.id], {'location_src_id': bom_point.routing_id.location_id.id})

            factor = production.product_qty * production.product_uom.factor / bom_point.product_uom.factor
            res = self.pool.get('mrp.bom')._bom_explode(cr, uid, bom_point, factor / bom_point.product_qty, properties)
            #self.pool.get('mrp.bom')._bom_compute_parameters(cr, uid, bom_point, production.order_line_id, properties)
            self.pool.get('mrp.bom')._bom_compute_parameters(cr, uid, bom_point, glob_orderid, properties)
            
            results = res[0]
            results2 = res[1]
            for line in results:
                line['production_id'] = production.id
                self.pool.get('mrp.production.product.line').create(cr, uid, line)
            for line in results2:
                line['production_id'] = production.id
                self.pool.get('mrp.production.workcenter.line').create(cr, uid, line)
        return len(results)

    def action_confirm(self, cr, uid, ids):
        ## debug roberto
        print '-----------------\n'
        print 'action_confirm(mrp production)\n'
        print '-----------------\n'
        ## fine debug roberto
        picking_id=False
        proc_ids = []
        for production in self.browse(cr, uid, ids):
            if not production.product_lines:
                self.action_compute(cr, uid, [production.id])
                production = self.browse(cr, uid, [production.id])[0]
            routing_loc = None
            pick_type = 'internal'
            address_id = False
            if production.bom_id.routing_id and production.bom_id.routing_id.location_id:
                routing_loc = production.bom_id.routing_id.location_id
                if routing_loc.usage<>'internal':
                    pick_type = 'out'
                address_id = routing_loc.location_id and routing_loc.location_id.id or False #address_id = routing_loc.address_id and routing_loc.address_id.id or False
                routing_loc = routing_loc.id
            picking_id = self.pool.get('stock.picking').create(cr, uid, {
                'origin': (production.origin or '').split(':')[0] +':'+production.name,
                'type': pick_type,
                'move_type': 'one',
                'state': 'auto',
                'location_id': address_id, #'address_id': address_id,
                'auto_picking': self._get_auto_picking(cr, uid, production),
            })

            source = production.product_id.product_tmpl_id.property_stock_production.id
            data = {
                'name':'PROD:'+production.name,
                #'date_expected': production.date_expected, ##'date_planned': production.date_planned,
                'product_id': production.product_id.id,
                'product_qty': production.product_qty,
                'product_uom': production.product_uom.id,
                'product_uos_qty': production.product_uos and production.product_uos_qty or False,
                'product_uos': production.product_uos and production.product_uos.id or False,
                'location_id': source,
                'location_dest_id': production.location_dest_id.id,
                'move_dest_id': production.move_prod_id.id,
                'state': 'waiting'
            }
            res_final_id = self.pool.get('stock.move').create(cr, uid, data)

            self.write(cr, uid, [production.id], {'move_created_ids': [(6, 0, [res_final_id])]})
            moves = []
            for line in production.product_lines:
                move_id=False
                newdate = production.date_planned
                if line.product_id.type in ('product', 'consu'):
                    res_dest_id = self.pool.get('stock.move').create(cr, uid, {
                        'name':'PROD:'+production.name,
                        #'date_expected': production.date_expected, ##'date_planned': production.date_planned,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos and line.product_uos_qty or False,
                        'product_uos': line.product_uos and line.product_uos.id or False,
                        'location_id': routing_loc or production.location_src_id.id,
                        'location_dest_id': source,
                        'move_dest_id': res_final_id,
                        'state': 'waiting',
                    })
                    moves.append(res_dest_id)
                    move_id = self.pool.get('stock.move').create(cr, uid, {
                        'name':'PROD:'+production.name,
                        'picking_id':picking_id,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos and line.product_uos_qty or False,
                        'product_uos': line.product_uos and line.product_uos.id or False,
                        'date_expected': newdate, ##'date_planned': newdate,
                        'move_dest_id': res_dest_id,
                        'location_id': production.location_src_id.id,
                        'location_dest_id': routing_loc or production.location_src_id.id,
                        'state': 'waiting',
                    })
                
                    proc_id = self.pool.get('procurement.order').create(cr, uid, {
                        'name': (production.origin or '').split(':')[0] + ':' + production.name,
                        'origin': (production.origin or '').split(':')[0] + ':' + production.name,
                        'date_planned': newdate,
                        'product_id': line.product_id.id,
                        'product_qty': line.product_qty,
                        'product_uom': line.product_uom.id,
                        'product_uos_qty': line.product_uos and line.product_qty or False,
                        'product_uos': line.product_uos and line.product_uos.id or False,
                        'location_id': production.location_src_id.id,
                        'procure_method': line.product_id.procure_method,
                        'move_id': move_id,
                        'order_line_id': production.order_line_id,
                    })
                wf_service = netsvc.LocalService("workflow")
                wf_service.trg_validate(uid, 'procurement.order', proc_id, 'button_confirm', cr)
                proc_ids.append(proc_id)
            wf_service = netsvc.LocalService("workflow")
            wf_service.trg_validate(uid, 'stock.picking', picking_id, 'button_confirm', cr)
            self.write(cr, uid, [production.id], {'picking_id':picking_id, 'move_lines': [(6,0,moves)], 'state':'confirmed'})
        return picking_id

mrp_production()


#-----------------------------------------------------------------------------
# Module: sale
#-----------------------------------------------------------------------------

# Create the object containing the parameter values associated to the sale order line.

class sale_order_line_parameter(osv.osv):
    _name = 'sale.order.line.parameter'
    _description = 'Parameters Values'
    _columns = {
        'parameter_id': fields.many2one('product.parameter','Name', readonly=True),
        'value': fields.float('Value', digits=(16,2), readonly=True),
        'sale_line_id': fields.many2one('sale.order.line', 'Order Line'),
    }

   
sale_order_line_parameter()

# Add a new field to the sale order lines which will contain the parameter values references.

class sale_order_line(osv.osv):
    _inherit = 'sale.order.line'
    _columns = {
        'parameter_ids': fields.one2many('sale.order.line.parameter', 'sale_line_id', 'Parameters Values', readonly=True),
    }
    _defaults = {
        'order_id': lambda self, cr, uid, context: context.get('order_id', False),}
 
    
    def button_confirm(self, cr, uid, ids, context=None):
        pool = pooler.get_pool(cr.dbname)
        orderline = self.pool.get('sale.order.line').browse(cr, uid, ids)[0]
        order_id = orderline.order_id
        order = pool.get('sale.order').browse(cr, uid, ids) [0]
        print 'ORDER ID:%s' % (order_id)
        print 'ORDER ID:%s' % (order)
        print 'ORDERLINE:%s' % (orderline)
        index = 0
        global glob_orderid
        ## debug roberto
        print '-----------------\n'
        print 'button_confirm(sale order line)\n'
        print '-----------------\n'
        ## fine debug roberto
        #print 'test MATH FLOOR:%s' % round(math.floor(4.88), 2)
        # update the parameters value for each sale order line
        #for line in orderline: #order.order_line:
        #print 'LINE ID:%s' % (line.id)
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(5,orderline.Larghezza,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(6,orderline.Altezza,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(7,orderline.Prof,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(8,orderline.INGSUP,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(9,orderline.INGINF,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(53,orderline.S1,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(54,orderline.S2,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(55,orderline.S3,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(56,orderline.S4,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(58,orderline.S5,orderline.id))
        cr.execute("""INSERT INTO sale_order_line_parameter(
            parameter_id, value, sale_line_id) VALUES (%s, %s, %s)""",(63,orderline.Ante,orderline.id))
            
        glob_orderid = orderline.id
        return self.write(cr, uid, ids, {'state': 'confirmed'})
    #return self.write(cr, uid, ids, {'state': 'confirmed','sale_line_id' : line.id})
sale_order_line()

# Specialize the action_ship_create method in the following way: before calling the base method,
# check that any parameters get their value; after calling the base method, update the procurement
# orders with the sale order line id and also insert the parameters values in mrp.parameters.

class sale(osv.osv):
    _inherit="sale.order"
    _columns = {
        'Acconto': fields.boolean('Acconto', help="ACCONTO ?"),
        'ImportoAcconto': fields.integer('Importoacconto', help="IMPORTO ACCONTO"),
    }

    def action_ship_create(self, cr, uid, ids, *args):

        ## debug roberto
        print '-----------------\n'
        print 'action_ship_create(sale order)1\n'
        print '-----------------\n'
        ## fine debug roberto
        
        # to begin with, check if the parameters have been set
        parametric_products = False
        parameters_set = False
        for order in self.browse(cr, uid, ids, context={}):
            for line in order.order_line:
                if line.product_id.parameters_ids:
                    parametric_products = True
                if line.parameter_ids:
                    parameters_set = True

        if parametric_products and (not parameters_set):
            raise osv.except_osv(('Parameters not set'),('Please set the value of the parametric products.'))

        ##debug roberto
        print '-----------------\n'
        print 'update mrp.parameters\n'
        print '-----------------\n'
        ## fine debug roberto
        
        for paramline_id in line.parameter_ids:
            self.pool.get('mrp.parameters').create(cr, uid, {
                'name': paramline_id.parameter_id.name,
                'value': paramline_id.value,
                'sale_line_id': paramline_id.sale_line_id.id,
            })


        ## debug roberto
        print '-----------------\n'
        print 'action_ship_create(sale order)2\n'
        print '-----------------\n'
        ## fine debug roberto

        # run action_ship_create of the superclass (procurements may be created)
        result = super(sale, self).action_ship_create(cr, uid, ids, *args)
        # now, update each procurement that has been created with the id of the sale order line
        # matched contains the id of the updated procurements
        for order in self.browse(cr, uid, ids, context={}):
            matched = []
            for line in order.order_line:
                procurement_ids = self.pool.get('procurement.order').search(cr, uid, [('origin','=',order.name),('product_id','=',line.product_id.id)])
                if procurement_ids:
                    procurements = self.pool.get('procurement.order').browse(cr, uid, procurement_ids)
                    for p in procurements:
                        if not p.id in matched:
                            matched.append(p.id)
                            self.pool.get('procurement.order').write(cr, uid, [p.id], {
                                'order_line_id': line.id,
                                })
                            break
                    # in addition, update mrp.parameters with these initial parameters values (later, it will
                    # also contain the formula results)

##                    ##debug roberto
##                    print '-----------------\n'
##                    print 'update mrp.parameters\n'
##                    print '-----------------\n'
##                    ## fine debug roberto
##                    
##                    for paramline_id in line.parameter_ids:
##                        self.pool.get('mrp.parameters').create(cr, uid, {
##                            'name': paramline_id.parameter_id.name,
##                            'value': paramline_id.value,
##                            'sale_line_id': paramline_id.sale_line_id.id,
##                        })
        ## debug roberto
        print '-----------------\n'
        print 'action_ship_create(sale order)3\n'
        print '-----------------\n'
        ## fine debug roberto
                        
        for order in self.browse(cr, uid, ids, context={}):
        # matched contains the id of the updated procurements
            matched = []
            for line in order.order_line:
                procurement_ids = self.pool.get('mrp.production').search(cr, uid, [('origin','=',order.name),('product_id','=',line.product_id.id)])
                if procurement_ids:
                    procurements = self.pool.get('mrp.production').browse(cr, uid, procurement_ids)
                    for p in procurements:
                        if not p.id in matched:
                            matched.append(p.id)
                            self.pool.get('mrp.production').write(cr, uid, [p.id], {
                                'order_line_id': line.id,
                                'Larghezza': line.Larghezza,
                                'Altezza': line.Altezza,
                                'Prof': line.Prof,
                                'INGSUP': line.INGSUP,
                                'INGINF': line.INGINF,
                                'S1': line.S1,
                                'S2': line.S2,
                                'S3': line.S3,
                                'S4': line.S4,
                                'S5': line.S5,
                                'Ante': line.Ante,
                                'Disegno': line.Disegno.id,
                                })
                            break
        return result
sale()

##
## METAL Model by RZ ################################################################################################################
##

class sale_order_line(osv.Model):

    def _div_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            #price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            #taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            #cur = line.order_id.pricelist_id.currency_id
            #res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id] = line.INGSUP + line.INGINF
        return res
    
    _name = 'sale.order.line'
    _inherit = 'sale.order.line'
    _columns = {
        'Disegno': fields.many2one('product.product', 'Disegno', domain=[('sale_ok', '=', False)]),
        'Colore' : fields.char('Colore', size=30, help="COLORE VERNICIATURA"),
        'Larghezza': fields.integer('Largh', help="BASE"),
        'Altezza': fields.integer('Alt', help="ALTEZZA"),
        'Prof': fields.integer('Prof', help="PROFONDITA'"),
        'INGSUP': fields.integer('INGSUP', help="INGOMBRO SUPERIORE"),
        'INGINF': fields.integer('INGINF', help="INGOMBRO INFERIORE"),
        #'Divisore': fields.integer('Divisore', help="DIVISORE"),

        'Divisore': fields.function(_div_line, string='Divisore', digits_compute= dp.get_precision('Account')),
        
        'Fermi': fields.boolean('Fermi', help="FERMI ?"),
        'Fissasicur': fields.boolean('FissaSICUR', help="FISSA SICUR ?"),
        'Fissapancia': fields.boolean('Fissa con pancia', help="FISSA con PANCIA ?"),
        'Fissaregolatore': fields.boolean('Fissa con regolatore', help="FISSA con REGOLATORE ?"),
        'Tipo': fields.selection([('Portafinestra','PORTAFINESTRA'), ('Finestra','FINESTRA')], 'Tipo', required=False,
            help="Specificare se si tratta di Porta o Porta/Finestra"),
        'Serpassante': fields.boolean('Ser.pass.', help="SERRATURA PASSANTE ?"),
        'S1': fields.integer('S1', help="Spazio 1(SX)"),
        'S2': fields.integer('S2', help="Spazio 2(intermedio o centrale)"),
        'S3': fields.integer('S3', help="Spazio 3(centrale o DX"),
        'S4': fields.integer('S4', help="Spazio 4(intermedio o DX)"),
        'S5': fields.integer('S5', help="Spazio 5(DX)"),
        'Ante': fields.integer('Numero Ante', help="Numero ANTE"),
    }

sale_order_line()

class mrp_production(osv.osv):
    _inherit = 'mrp.production'
    _columns = {
        'Larghezza': fields.integer('Largh', help="BASE"),
        'Altezza': fields.integer('Alt', help="ALTEZZA"),
        'Prof': fields.integer('Prof', help="PROFONDITA'"),
        'INGSUP': fields.integer('INGSUP', help="INGOMBRO SUPERIORE"),
        'INGINF': fields.integer('INGINF', help="INGOMBRO INFERIORE"),
        'S1': fields.integer('S1', help="Spazio 1(SX)"),
        'S2': fields.integer('S2', help="Spazio 2(intermedio o centrale)"),
        'S3': fields.integer('S3', help="Spazio 3(centrale o DX"),
        'S4': fields.integer('S4', help="Spazio 4(intermedio o DX)"),
        'S5': fields.integer('S5', help="Spazio 5(DX)"),
        'Ante': fields.integer('Numero Ante', help="Numero ANTE"),
        'Disegno': fields.many2one('product.product', 'Disegno', domain=[('sale_ok', '=', False)]),
        'workcenter_id': fields.many2one('mrp.workcenter', 'Work Center', required=False),
    }
    def assign_worktime(self, cr, uid, ids, context=None):
        """ Cancels the production order and related stock moves.
        @return: True
        """
        for production in self.browse(cr, uid, ids, context=context):
            if production.state not in ('draft', 'cancel','ready'):
                raise osv.except_osv('Invalid Action!','Impossibile assegnare il tempo di lavoro per un ordine di produzione in stato "%s".' % (production.state))
            else:
                print 'WORKCENTER ID:%s nome:%s' % (production.workcenter_id.id,production.workcenter_id.name)
                workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
                for production in self.browse(cr, uid, ids):
                    print 'PRODUCTION ORDER:%s' % (production.id)
                    cr.execute('UPDATE mrp_production_workcenter_line SET workcenter_id=%s WHERE production_id=%s and workcenter_id<>2',(production.workcenter_id.id,production.id))

                    
        return True
mrp_production()

class stock_move(osv.osv):

    def _par_line(self, cr, uid, ids, field_name, arg, context=None):
        tax_obj = self.pool.get('account.tax')
        cur_obj = self.pool.get('res.currency')
##        Tlargh = self.pool.get('mrp.production').browse(cr, uid, ids, context=context).Larghezza
        
        res = {}
        if context is None:
            context = {}
        for line in self.browse(cr, uid, ids, context=context):
            #price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
            #taxes = tax_obj.compute_all(cr, uid, line.tax_id, price, line.product_uom_qty, line.product_id, line.order_id.partner_id)
            #cur = line.order_id.pricelist_id.currency_id
            #res[line.id] = cur_obj.round(cr, uid, cur, taxes['total'])
            res[line.id] = line.price_unit * 100.0
        return res

    _inherit = 'stock.move'
    _columns = {
        'Larghezza': fields.function(_par_line, string='Largh', digits_compute= dp.get_precision('Account')),
        #'Larghezza': fields.integer('Largh', help="BASE"),
    }
stock_move()

