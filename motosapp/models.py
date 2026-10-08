from django.db import models

# Create your models here.
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinValueValidator, MaxValueValidator


# =========================================================
# USUARIOS Y ROLES
# =========================================================
class Rol(models.Model):
    nombre = models.CharField(max_length=50, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'roles'

    def __str__(self):
        return self.nombre


class Usuario(AbstractUser):
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, blank=True)
    telefono = models.CharField(max_length=30, blank=True)

    class Meta:
        db_table = 'usuarios'

    def __str__(self):
        return self.username


# =========================================================
# CATÁLOGO DE MOTOS
# =========================================================
class Marca(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    pais_origen = models.CharField(max_length=80, blank=True)
    logo_url = models.URLField(blank=True)

    class Meta:
        db_table = 'marcas'

    def __str__(self):
        return self.nombre


class Categoria(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'categorias'
        verbose_name_plural = 'Categorias'

    def __str__(self):
        return self.nombre


class Modelo(models.Model):
    marca = models.ForeignKey(Marca, on_delete=models.CASCADE, related_name='modelos')
    categoria = models.ForeignKey(Categoria, on_delete=models.CASCADE, related_name='modelos')
    nombre = models.CharField(max_length=120)
    anio = models.PositiveSmallIntegerField(null=True, blank=True)
    cilindraje = models.PositiveIntegerField(null=True, blank=True)
    tipo_motor = models.CharField(max_length=50, blank=True)
    potencia_hp = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    precio_referencia = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = 'modelos'
        unique_together = ('marca', 'nombre', 'anio')

    def __str__(self):
        return f"{self.marca.nombre} {self.nombre} ({self.anio})"


class Moto(models.Model):
    CONDICION_CHOICES = [('nueva', 'Nueva'), ('usada', 'Usada')]
    ESTADO_CHOICES = [
        ('disponible', 'Disponible'),
        ('reservada', 'Reservada'),
        ('vendida', 'Vendida'),
        ('taller', 'En taller'),
    ]

    modelo = models.ForeignKey(Modelo, on_delete=models.PROTECT, related_name='motos')
    vin = models.CharField(max_length=50, unique=True, blank=True, null=True)
    numero_motor = models.CharField(max_length=50, unique=True, blank=True, null=True)
    placa = models.CharField(max_length=20, unique=True, blank=True, null=True)
    color = models.CharField(max_length=40, blank=True)
    anio_fabricacion = models.PositiveSmallIntegerField(null=True, blank=True)
    kilometraje = models.PositiveIntegerField(default=0)
    condicion = models.CharField(max_length=10, choices=CONDICION_CHOICES, default='nueva')
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='disponible')
    proveedor = models.ForeignKey(
        'Proveedor', on_delete=models.SET_NULL, null=True, blank=True, related_name='motos'
    )
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'motos'

    def __str__(self):
        return f"{self.modelo} - {self.placa or self.vin or self.id}"


# =========================================================
# CLIENTES Y PROVEEDORES
# =========================================================
class Cliente(models.Model):
    usuario = models.OneToOneField(
        Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='cliente'
    )
    tipo_documento = models.CharField(max_length=20, blank=True)
    numero_documento = models.CharField(max_length=30, unique=True, blank=True, null=True)
    nombres = models.CharField(max_length=100)
    apellidos = models.CharField(max_length=100, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    fecha_registro = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'clientes'

    def __str__(self):
        return f"{self.nombres} {self.apellidos}".strip()


class Proveedor(models.Model):
    nombre = models.CharField(max_length=120)
    contacto = models.CharField(max_length=120, blank=True)
    telefono = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    direccion = models.CharField(max_length=255, blank=True)
    ciudad = models.CharField(max_length=80, blank=True)
    ruc_nit = models.CharField(max_length=30, unique=True, blank=True, null=True)

    class Meta:
        db_table = 'proveedores'

    def __str__(self):
        return self.nombre


# =========================================================
# REPUESTOS Y SERVICIOS
# =========================================================
class CategoriaRepuesto(models.Model):
    nombre = models.CharField(max_length=80, unique=True)
    descripcion = models.CharField(max_length=255, blank=True)

    class Meta:
        db_table = 'categorias_repuesto'

    def __str__(self):
        return self.nombre


class Repuesto(models.Model):
    codigo = models.CharField(max_length=50, unique=True)
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    categoria = models.ForeignKey(
        CategoriaRepuesto, on_delete=models.SET_NULL, null=True, related_name='repuestos'
    )
    marca = models.ForeignKey(
        Marca, on_delete=models.SET_NULL, null=True, blank=True, related_name='repuestos'
    )
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    precio_venta = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    stock = models.IntegerField(default=0)
    stock_minimo = models.IntegerField(default=5)
    ubicacion = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = 'repuestos'

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"


class Servicio(models.Model):
    nombre = models.CharField(max_length=120)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    duracion_estimada = models.PositiveIntegerField(help_text='Minutos', default=30)

    class Meta:
        db_table = 'servicios'

    def __str__(self):
        return self.nombre


# =========================================================
# VENTAS
# =========================================================
class Venta(models.Model):
    ESTADO_CHOICES = [
        ('pendiente', 'Pendiente'),
        ('pagada', 'Pagada'),
        ('anulada', 'Anulada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ventas')
    empleado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name='ventas_realizadas'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=15, choices=ESTADO_CHOICES, default='pendiente')

    class Meta:
        db_table = 'ventas'
        ordering = ['-fecha']

    def __str__(self):
        return f"Venta #{self.id} - {self.cliente}"


class DetalleVenta(models.Model):
    PRODUCTO_TIPO = [
        ('moto', 'Moto'),
        ('repuesto', 'Repuesto'),
        ('servicio', 'Servicio'),
    ]

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto_tipo = models.CharField(max_length=10, choices=PRODUCTO_TIPO)
    moto = models.ForeignKey(Moto, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    servicio = models.ForeignKey(Servicio, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    descuento = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'detalle_ventas'

    def __str__(self):
        return f"{self.producto_tipo} x{self.cantidad}"


class Pago(models.Model):
    METODO_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('credito', 'Crédito'),
    ]

    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='pagos')
    fecha = models.DateTimeField(auto_now_add=True)
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    metodo = models.CharField(max_length=20, choices=METODO_CHOICES)
    referencia = models.CharField(max_length=100, blank=True)
    estado = models.CharField(max_length=15, default='confirmado')

    class Meta:
        db_table = 'pagos'

    def __str__(self):
        return f"Pago {self.monto} - Venta #{self.venta_id}"


class Factura(models.Model):
    venta = models.OneToOneField(Venta, on_delete=models.CASCADE, related_name='factura')
    numero_factura = models.CharField(max_length=30, unique=True)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    estado = models.CharField(max_length=15, default='emitida')

    class Meta:
        db_table = 'facturas'

    def __str__(self):
        return self.numero_factura


# =========================================================
# COMPRAS
# =========================================================
class Compra(models.Model):
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name='compras')
    empleado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name='compras_realizadas'
    )
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    impuesto = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    estado = models.CharField(max_length=15, default='recibida')

    class Meta:
        db_table = 'compras'

    def __str__(self):
        return f"Compra #{self.id} - {self.proveedor}"


class DetalleCompra(models.Model):
    PRODUCTO_TIPO = [('moto', 'Moto'), ('repuesto', 'Repuesto')]

    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto_tipo = models.CharField(max_length=10, choices=PRODUCTO_TIPO)
    moto = models.ForeignKey(Moto, on_delete=models.SET_NULL, null=True, blank=True)
    repuesto = models.ForeignKey(Repuesto, on_delete=models.SET_NULL, null=True, blank=True)
    cantidad = models.PositiveIntegerField(default=1)
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    class Meta:
        db_table = 'detalle_compras'


# =========================================================
# TALLER
# =========================================================
class OrdenTaller(models.Model):
    ESTADO_CHOICES = [
        ('recibida', 'Recibida'),
        ('diagnosticada', 'Diagnosticada'),
        ('en_reparacion', 'En reparación'),
        ('terminada', 'Terminada'),
        ('entregada', 'Entregada'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name='ordenes_taller')
    moto = models.ForeignKey(Moto, on_delete=models.PROTECT, related_name='ordenes_taller')
    empleado = models.ForeignKey(
        Usuario, on_delete=models.SET_NULL, null=True, related_name='ordenes_asignadas'
    )
    fecha_ingreso = models.DateTimeField(auto_now_add=True)
    fecha_estimada = models.DateField(null=True, blank=True)
    fecha_entrega = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_CHOICES, default='recibida')
    diagnostico = models.TextField(blank=True)
    observaciones = models.TextField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        db_table = 'ordenes_taller'
        ordering = ['-fecha_ingreso']

    def __str__(self):
        return f"Orden #{self.id} - {self.moto}"


class DetalleOrdenServicio(models.Model):
    orden = models.ForeignKey(OrdenTaller, on_delete=models.CASCADE, related_name='servicios')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_orden_servicio'


class DetalleOrdenRepuesto(models.Model):
    orden = models.ForeignKey(OrdenTaller, on_delete=models.CASCADE, related_name='repuestos')
    repuesto = models.ForeignKey(Repuesto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField(default=1)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'detalle_orden_repuesto'


# =========================================================
# EXTRAS
# =========================================================
class Resena(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE, related_name='resenas')
    modelo = models.ForeignKey(Modelo, on_delete=models.CASCADE, related_name='resenas')
    calificacion = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comentario = models.TextField(blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'resenas'
        unique_together = ('cliente', 'modelo')

    def __str__(self):
        return f"{self.cliente} → {self.modelo} ({self.calificacion}★)"