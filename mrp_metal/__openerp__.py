{
    "name" : "Metal Products",
    "version" : "0.1 for Open ERP 7",
    "author" : "Roberto Zanardo",
    "website" : "http://www.progressive.it/",
    "description": """
This Module add fields to manage metal windows production from sale orders to mrp
    """,
    "depends" : [
                 "base", "product", "mrp", "sale", "procurement"
    ],
    "data": [
        'mrp_metal.xml','product_parametric_view.xml',"product_parametric_report.xml","sale_report_new.xml",
    ],
    'installable': True,
    "active": True,
}
