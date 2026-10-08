from django.contrib import admin
# Register your models here.
from .models import (
    Rol, Usuario, Marca, Categoria, Modelo, Moto,
    Cliente, Proveedor, Repuesto, Servicio,
    Venta, DetalleVenta, Pago, Factura,
    OrdenTaller, DetalleOrdenServicio, DetalleOrdenRepuesto,
    Resena, CategoriaRepuesto,
)

admin.site.register(Rol)
admin.site.register(Usuario)
admin.site.register(Marca)
admin.site.register(Categoria)
admin.site.register(Modelo)
admin.site.register(Moto)
admin.site.register(Cliente)
admin.site.register(Proveedor)
admin.site.register(Repuesto)
admin.site.register(Servicio)
admin.site.register(Venta)
admin.site.register(DetalleVenta)
admin.site.register(Pago)
admin.site.register(Factura)
admin.site.register(OrdenTaller)
admin.site.register(DetalleOrdenServicio)
admin.site.register(DetalleOrdenRepuesto)
admin.site.register(Resena)
admin.site.register(CategoriaRepuesto)