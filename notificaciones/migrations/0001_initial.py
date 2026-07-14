from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name='Cliente',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nombre', models.CharField(max_length=200, verbose_name='Nombre del negocio')),
                ('api_key', models.CharField(max_length=64, unique=True, verbose_name='API Key')),
                ('email_from', models.EmailField(blank=True, verbose_name='Email remitente')),
                ('sendgrid_api_key', models.CharField(blank=True, max_length=300, verbose_name='SendGrid API Key')),
                ('whatsapp_token', models.CharField(blank=True, max_length=500, verbose_name='WhatsApp Token (Meta)')),
                ('whatsapp_phone_id', models.CharField(blank=True, max_length=50, verbose_name='WhatsApp Phone Number ID')),
                ('activo', models.BooleanField(default=True, verbose_name='Activo')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={
                'verbose_name': 'Cliente',
                'verbose_name_plural': 'Clientes',
                'ordering': ['nombre'],
            },
        ),
        migrations.CreateModel(
            name='Notificacion',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('evento', models.CharField(max_length=50, verbose_name='Evento')),
                ('canal', models.CharField(
                    choices=[('email', 'Email'), ('whatsapp', 'WhatsApp')],
                    max_length=20, verbose_name='Canal',
                )),
                ('destinatario', models.CharField(max_length=300, verbose_name='Destinatario')),
                ('contexto', models.JSONField(default=dict, verbose_name='Contexto')),
                ('estado', models.CharField(
                    choices=[
                        ('pendiente', 'Pendiente'), ('enviado', 'Enviado'),
                        ('error', 'Error'), ('descartado', 'Descartado'),
                    ],
                    db_index=True, default='pendiente', max_length=20, verbose_name='Estado',
                )),
                ('intentos', models.IntegerField(default=0, verbose_name='Intentos')),
                ('enviado_at', models.DateTimeField(blank=True, null=True, verbose_name='Enviado en')),
                ('error_mensaje', models.TextField(blank=True, verbose_name='Detalle del error')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('cliente', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='notificaciones', to='notificaciones.cliente',
                )),
            ],
            options={
                'verbose_name': 'Notificación',
                'verbose_name_plural': 'Notificaciones',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='notificacion',
            index=models.Index(fields=['estado', 'intentos'], name='notificacio_estado_intentos_idx'),
        ),
    ]
