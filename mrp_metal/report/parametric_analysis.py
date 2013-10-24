##############################################################################
#
#    Parametric Products, version 1.0
#    Compatible with OpenERP release 5.0.0
#    Copyright (C) 2009 Andrea Polla. All Rights Reserved.
#    Email: apolla@libero.it
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

import time
import pooler
from report import report_sxw

class parametric_analysis_print(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        super(parametric_analysis_print, self).__init__(cr, uid, name, context)
        self.localcontext.update({
           'get_parid': self._get_parid,
           'get_parameters': self._get_parameters,
           'time': time,
        })
        self.found = []

    def _get_parameters(self, order, product):
        pool = pooler.get_pool(self.cr.dbname)
        res = ''
##        fout =''
##        f = open('D:/testwritefile.txt','w')

        if product.parameters_ids:
            for param_id in product.parameters_ids:
                if res:
                   res += '\n'
                pvalue = 0.0
                paramline_ids = pool.get('mrp.parameters').search(
                    self.cr,self.uid,[('sale_line_id','=',order.order_line_id),('name','=',param_id.name)])
                
##                fout +='order.order_line_id: %s' % (order.order_line_id)
##                fout += '\n'
##                fout +='name: %s' % (param_id.name)
##                fout += '\n'
##                f.write(fout)
                
                if paramline_ids:
                    params = self.pool.get('procurement.order').browse(self.cr, self.uid, paramline_ids)
                    for p in params:
##                        fout +='p: %s' % (p.id)
##                        fout += '\n'
                        if not p.id in self.found:
                            self.found.append(p.id)
                            val = pool.get('mrp.parameters').read(self.cr, self.uid, [p.id], ['value'])
                            pvalue = val[0]['value'] or 0.0
                            break
                        
                #res += '%s %s = %.2f %s' % (p.product_qty,param_id.description, pvalue, param_id.uom_id.name)
                if ((param_id.id != 61) and (param_id.id != 67) and (param_id.id != 64) and (param_id.id != 65)and (param_id.id != 66) and (param_id.id != 81) and (param_id.id != 82)and (param_id.id != 98)):
                    res += '%s = %.2f %s' % (str.upper(param_id.description.encode('ascii','ignore')), pvalue, param_id.uom_id.name)
                    #res += '%s %s = %.2f %s' % (param_id.id,param_id.description, pvalue, param_id.uom_id.name)
                else:
                    res += ''
                #fout+='param_id.description: %s' % (param_id.description)
##                fout += '\n'
##                fout += '-----------------------------------------------'
##                fout += '\n'
##                f.write(fout)
##                
##        f.close()
        return res

    def _get_parid(self, order, product):
        pool = pooler.get_pool(self.cr.dbname)
        res = ''
        if product.parameters_ids:
            for param_id in product.parameters_ids:
                if res:
                   res += '\n'
                pvalue = 0.0
                paramline_ids = pool.get('mrp.parameters').search(
                    self.cr,self.uid,[('sale_line_id','=',order.order_line_id),('name','=',param_id.name)])
                if paramline_ids:
                    params = self.pool.get('procurement.order').browse(self.cr, self.uid, paramline_ids)
                    for p in params:
                        if not p.id in self.found:
                            self.found.append(p.id)
                            val = pool.get('mrp.parameters').read(self.cr, self.uid, [p.id], ['value'])
                            pvalue = val[0]['value'] or 0.0
                            break
                res += '%s' % (param_id.id)
        return res

report_sxw.report_sxw('report.parametric.analysis.print',
                      'mrp.production',
                      'addons/product_parametric/report/parametric_analysis.rml',
                      parser=parametric_analysis_print,
                      header=1)
