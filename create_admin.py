import os
import sys
import django

# Configura o ambiente Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'petshop_project.settings')
django.setup()

# Agora podemos importar os modelos
from django.contrib.auth.models import User

def create_admin_user():
    # Verifica se o usuário admin já existe
    if not User.objects.filter(username='admin').exists():
        # Cria o superusuário
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
    else:
        print("O usuário 'admin' já existe no sistema.")

if __name__ == "__main__":
    create_admin_user()
