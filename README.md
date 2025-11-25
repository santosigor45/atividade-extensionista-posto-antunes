# Posto Antunes

<table width="100%">
  <thead>
    <tr>
      <th width="50%">Início</th>
      <th width="50%">Menu</th>
    </tr>
  </thead>
  <tbody>
    <tr>
      <td width="50%"><img alt="Página inicial" src="/art/screenshot-1.png" /></td>
      <td width="50%"><img alt="Menu" src="/art/screenshot-2.png" /></td>
    </tr>
  </tbody>
</table>

## Visão Geral
Posto Antunes é uma Progressive Web Application (PWA) que facilita o controle de abastecimentos em frotas — especialmente pensada para transporte escolar.

Principais objetivos:
- Registrar e validar abastecimentos e entregas de combustível (validação no frontend e backend para reduzir erros);
- Armazenar dados de forma segura em MySQL;
- Oferecer painel administrativo com autenticação para gerenciamento de registros, consultas e gráficos gerenciais.

O aplicativo também foi projetado para ser usado em navegadores modernos como PWA, melhorando a experiência em dispositivos móveis e em situações com conectividade limitada.

## Funcionalidades
- **Coleta e validação de dados**: captura informações de abastecimento via formulário, com validação completa no frontend e backend para reduzir erros de digitação.
- **Armazenamento de dados**: todos os dados coletados são armazenados com segurança em banco de dados MySQL.
- **Autenticação e painel administrativo**: login de usuários e dashboard administrativo para gestão e acompanhamento dos dados.

## Instalação
É necessário ter Python instalado no sistema (recomendado Python 3.13). Depois, instale as dependências com o pip:

    pip install -r requirements.txt

## Uso
- **Iniciar a aplicação:** execute localmente em http://127.0.0.1:5000 com:

        flask --app application run

## Configuração
Defina as variáveis de ambiente necessárias para conexão com o banco e segurança da aplicação em um arquivo .env ou através dos comandos abaixo:
    
    export MYSQL_URL=mysql+pymysql://user@localhost/db_name
    export PERMANENT_SESSION_LIFETIME='31536000'
    export SECRET_KEY=strong_secret_key

## Banco de Dados (dump incluído)
Um snapshot do MySQL está na raiz: `posto_antunes_dump.sql`.

Para restaurar localmente:
1) Suba o serviço MySQL.
2) Crie o banco (se ainda não existir):  
   `mysql -u <usuario> -p -e "CREATE DATABASE IF NOT EXISTS posto_antunes CHARACTER SET utf8mb4;"`
3) Importe o dump:  
   `mysql -u <usuario> -p posto_antunes < posto_antunes_dump.sql`
4) Ajuste o `.env` para apontar para esse banco, por exemplo:  
   `MYSQL_URL=mysql+pymysql://<usuario>@localhost/posto_antunes`

## Contato
Em caso de dúvidas ou suporte, envie um e-mail para santosigor45@gmail.com.
