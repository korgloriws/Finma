<<<<<<< HEAD
# Finma - Sistema de Gestão Financeira e Investimentos

## 📋 Descrição

O **Finma** é um sistema completo de gestão financeira e análise de investimentos desenvolvido em Python com Dash/Flask. O sistema oferece funcionalidades para controle financeiro pessoal, análise de ativos da B3, gestão de carteira de investimentos e assistente de IA integrado.

## 🚀 Funcionalidades Principais

### 💰 Controle Financeiro
- Gestão de receitas e despesas
- Controle de cartões de crédito
- Acompanhamento de saldo mensal
- Categorização de gastos

### 📊 Análise de Investimentos
- Análise de ações, BDRs e FIIs da B3
- Filtros por indicadores fundamentais (P/L, P/VP, ROE, Dividend Yield)
- Rankings de ativos
- Gráficos interativos de performance

### 🎯 Gestão de Carteira
- Cadastro de ativos na carteira
- Acompanhamento de movimentações
- Cálculo de rentabilidade
- Histórico de performance

### 🤖 Assistente de IA
- Análise inteligente do contexto financeiro
- Sugestões personalizadas
- Alertas automáticos
- Respostas a perguntas sobre finanças

### 📈 Visualizações
- Gráficos interativos com Plotly
- Dashboards personalizáveis
- Modo escuro/claro
- Responsivo para diferentes dispositivos

## 🛠️ Requisitos do Sistema

### Software Necessário
- **Python 3.11** ou superior
- **Git** (para clonar o repositório)

### Hardware Recomendado
- **RAM**: Mínimo 8GB (recomendado 16GB+ para IA)
- **Armazenamento**: 10GB livres (incluindo modelo de IA)
- **Processador**: Intel i5/AMD Ryzen 5 ou superior

## 📦 Instalação

### 1. Clone o Repositório
```bash
git clone <url-do-repositorio>
cd finma_2.8_Copia
```

### 2. Crie um Ambiente Virtual
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências Python

**Opção A: Instalação Rápida (Recomendada)**
```bash
pip install -r requirements.txt
```

**Opção B: Instalação Manual**
```bash
pip install dash
pip install dash-bootstrap-components
pip install pandas
pip install yfinance
pip install flask
pip install flask-caching
pip install plotly
pip install bcrypt
pip install requests
pip install tqdm
```

### 4. Instale o Llama-cpp-python (para IA)
```bash
# Windows (usando o arquivo .whl incluído)
pip install llama_cpp_python-0.2.24-cp311-cp311-win_amd64.whl

# Linux/Mac
pip install llama-cpp-python
```

### 5. Baixe o Modelo de IA
```bash
python modelos/baixar_modelo.py
```

**Nota**: O download do modelo pode demorar alguns minutos e requer aproximadamente 4GB de espaço.

## 🚀 Como Executar

### 1. Ative o Ambiente Virtual
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### 2. Execute o Sistema
```bash
python app.py
```

### 3. Acesse a Aplicação
Abra seu navegador e acesse: `http://localhost:5000`

## 📁 Estrutura do Projeto

```
finma_2.8_Copia/
├── app.py                 # Aplicação principal
├── models.py              # Modelos de dados e lógica de negócio
├── complete_b3_logos_mapping.py  # Mapeamento de logos da B3
├── assets/                # Arquivos CSS e recursos
│   ├── custom_logos.css
│   └── dark_theme.css
├── pages/                 # Módulos da aplicação
│   ├── analise.py         # Análise de ativos
│   ├── assistente_ia.py   # Assistente de IA
│   ├── carteira.py        # Gestão de carteira
│   ├── controle.py        # Controle financeiro
│   ├── detalhes.py        # Detalhes dos ativos
│   ├── graficos.py        # Visualizações
│   ├── lista.py           # Lista de ativos
│   ├── marmitas.py        # Gestão de marmitas
│   └── rankers.py         # Rankings
├── modelos/               # Modelos de IA
│   ├── baixar_modelo.py
│   └── mistral-7b-instruct-v0.1.Q4_K_M.gguf
└── *.db                   # Bancos de dados SQLite
```

## 🗄️ Bancos de Dados

O sistema utiliza bancos SQLite para armazenar dados:

- **carteira.db**: Dados da carteira de investimentos
- **financeiro.db**: Dados financeiros (receitas, despesas, cartões)
- **marmitas.db**: Dados de gestão de marmitas
- **logo_cache.db**: Cache de logos da B3

## 🔧 Configuração

### Variáveis de Ambiente (Opcional)
```bash
# Para desenvolvimento
export FLASK_ENV=development
export FLASK_DEBUG=1
```

### Personalização
- Modifique `assets/custom_logos.css` para personalizar o visual
- Ajuste `assets/dark_theme.css` para customizar o modo escuro
- Edite `models.py` para modificar listas de ativos

## 📱 Uso do Sistema

### 1. Primeiro Acesso
- O sistema criará automaticamente as tabelas necessárias
- Comece cadastrando suas receitas e despesas no módulo "Controle Financeiro"

### 2. Gestão de Investimentos
- Use "Análise" para filtrar ativos da B3
- Adicione ativos à sua carteira em "Carteira"
- Acompanhe performance em "Gráficos"

### 3. Assistente de IA
- Acesse "Assistente IA" para análises inteligentes
- Faça perguntas sobre suas finanças
- Receba sugestões personalizadas

## 🐛 Solução de Problemas

### Erro de Importação
```bash
# Certifique-se de que o ambiente virtual está ativo
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac
```

### Erro no Modelo de IA
```bash
# Reinstale o llama-cpp-python
pip uninstall llama-cpp-python
pip install llama_cpp_python-0.2.24-cp311-cp311-win_amd64.whl
```

### Problemas de Performance
- Feche outras aplicações para liberar RAM
- O modelo de IA requer pelo menos 4GB de RAM disponível

### Erro de Conexão com Yahoo Finance
- Verifique sua conexão com a internet
- O sistema usa yfinance para obter dados de mercado

## 🔒 Segurança

- O sistema utiliza bcrypt para criptografia de senhas
- Dados são armazenados localmente em bancos SQLite
- Não há transmissão de dados financeiros para servidores externos

## 📊 Dados Utilizados

- **Yahoo Finance**: Dados de mercado em tempo real
- **B3**: Lista de ativos negociados
- **Mistral 7B**: Modelo de IA para análises

## 🤝 Contribuição

Para contribuir com o projeto:

1. Faça um fork do repositório
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📄 Licença

Este projeto está sob licença MIT. Veja o arquivo LICENSE para mais detalhes.

## 📞 Suporte

Para suporte técnico ou dúvidas:
- Abra uma issue no repositório
- Consulte a documentação das bibliotecas utilizadas

## 🔄 Atualizações

Para atualizar o sistema:
```bash
git pull origin main
pip install -r requirements.txt  # se houver
```

---

**Desenvolvido com ❤️ usando Python, Dash e Flask** 
=======
# Finma
>>>>>>> e1972aada9257f0d7851fd4a285752815007b20b
