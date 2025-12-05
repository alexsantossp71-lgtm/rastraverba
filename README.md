# RastraVerba

Plataforma de Jornalismo de Dados Serverless para rastrear Emendas Parlamentares ("Emendas Pix") usando APIs de Dados Abertos.

## Arquitetura

- **Frontend**: Next.js 14 (Static Export) hospedado no GitHub Pages
- **Query Engine**: DuckDB-Wasm (SQL no navegador)
- **Database**: Apache Parquet files
- **ETL**: Python scripts executados via GitHub Actions

## Estrutura

```
/etl                    # Scripts Python para ETL
/web                    # Aplicação Next.js
/data                   # Arquivos Parquet
/.github/workflows      # GitHub Actions
/.devcontainer          # Configuração Codespaces
```

## Desenvolvimento

### Via Codespaces
1. Clique em "Code" → "Open with Codespaces"
2. Aguarde a configuração automática

### Local
```bash
# ETL
pip install -r requirements.txt
python etl/main.py

# Frontend
cd web
npm install
npm run dev
```

## APIs Utilizadas

- [Câmara dos Deputados](https://dadosabertos.camara.leg.br/)
- [TransfereGov](https://api.transferegov.gestao.gov.br/)
- [Querido Diário](https://queridodiario.ok.org.br/api/)
