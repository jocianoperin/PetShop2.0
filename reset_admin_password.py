import os
import sys
import django

# Configura o ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

from django.contrib.auth.models import User

def reset_admin_password():
    try:
        # Busca o usuário admin
        admin = User.objects.get(username='admin')
        # Redefine a senha para 'admin'
        admin.set_password('admin')
        admin.save()
        print("Senha do usuário 'admin' foi redefinida para 'admin'")
        print("Agora você pode fazer login com:")
        print("Usuário: admin")
        print("Senha: admin")
        print("\nIMPORTANTE: Por segurança, altere esta senha após o primeiro login!")
    except User.DoesNotExist:
        print("Usuário 'admin' não encontrado. Criando novo usuário...")
        User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='admin',
            first_name='Administrador',
            last_name='do Sistema'
        )
        print("Usuário administrador criado com sucesso!")
        print("Usuário: admin")
        print("Senha: admin")
        print("\nIMPORTANTE: Altere esta senha após o primeiro login!")

if __name__ == "__main__":
    reset_admin_password()
