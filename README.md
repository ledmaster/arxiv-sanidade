# ArXiv Sanidade 🇧🇷

Inspirado pelo [arxiv-sanity-lite](https://arxiv-sanity-lite.com/) do Andrej Karpathy, ArXiv Sanidade é uma aplicação web que ajuda os usuários a descobrir e salvar artigos relevantes do arXiv usando machine learning.

Ele usa um modelo linear simples treinado nos artigos que o usuário salva explicitamente para prever a relevância de novos artigos.

## Recursos

* Exibe artigos recentes do arXiv de categorias específicas (Ciência da Computação, Estatística, Inteligência Artificial).
* Permite que os usuários salvem artigos de interesse.
* Usa um modelo de aprendizado de máquina (LinearSVC) para classificar os artigos com base na similaridade com os artigos salvos.
* Fornece uma interface simples para visualizar resumos de artigos e links para o PDF.
* Funcionalidade de copiar o ID do arXiv para a área de transferência.

## Detalhes Técnicos

* Construído com Flask (backend), HTML/CSS/JavaScript (frontend) e SQLite (banco de dados).
* Usa a API do arXiv para buscar artigos.
* Emprega a API do Google Gemini para gerar embeddings de texto.
* Usa scikit-learn para o modelo de aprendizado de máquina.
* Inclui filtragem de data para artigos do arXiv (opcional, usando o argumento `--days`).

## Instalação

1. Clone o repositório.
2. Instale os pacotes Python necessários: `pip install -r requirements.txt`
3. Defina a variável de ambiente `GEMINI_API_KEY` com sua chave de API do Gemini.
4. Execute o aplicativo: `python app.py [--days <número_de_dias>]` (isso criará o arquivo `papers.db`).

## Utilização

1. Abra o aplicativo web no seu navegador (o endereço padrão é `http://127.0.0.1:5000/`).
2. Espere carregar os artigos (parece que não está funcionando/travou, mas se você olhar no Terminal ele vai mostrando as mensagens de log enquanto carrega tudo).
3. Navegue pelos artigos listados.
4. Use o campo de entrada na parte superior para salvar um artigo por seu ID do arXiv.
5. Clique em "Salvar Paper" para adicionar artigos ao seu conjunto salvo e retreinar o modelo.
6. Clique em "View PDF" para abrir o artigo completo em uma nova guia.
7. Clique em "Copy Link" para copiar o ID do arXiv para a área de transferência.

## Primeiro Uso

A função `init_db` verifica se a tabela `saved_papers` está vazia no banco de dados `papers.db`.

Se estiver (como no primeiro uso), ela busca o artigo com o [ID 1603.02754 (XGBoost)](https://arxiv.org/abs/1603.02754) da API do arXiv e o insere no banco de dados como um artigo inicial.

Uma mensagem indica se o artigo inicial foi adicionado ou se um erro ocorreu.

## Detalhes Sobre A Classificação Com Machine Learning

A API do Google Gemini gera embeddings de texto, que são representações vetoriais das informações semânticas do texto.

No arxiv-sanity-lite, Karpathy usa Bag-of-Words simples com TF-IDF.

Esta versão utiliza embeddings para uma abordagem mais moderna.

No ArXiv Sanidade, o sistema gera embeddings para o título e resumo de cada artigo.

Esses vetores capturam a essência do conteúdo de cada artigo, permitindo que o modelo de machine learning compare a similaridade semântica entre os artigos. 

A API Gemini simplifica o processo, fornecendo embeddings de alta qualidade sem a necessidade de treinar e gerenciar modelos complexos de NLP.

O modelo de machine learning empregado é o LinearSVC (Linear Support Vector Classification) da biblioteca scikit-learn.

O modelo é treinado com os embeddings dos artigos salvos pelo usuário como exemplos positivos e os embeddings dos artigos recentes como exemplos negativos.

O LinearSVC aprende a classificar os artigos com base nesses exemplos, criando um hiperplano que separa os artigos relevantes dos irrelevantes no espaço vetorial dos embeddings.

A pontuação de cada artigo, exibida na interface, representa a distância do embedding do artigo até esse hiperplano, indicando a pontuação de relevância de acordo com o modelo treinado.

Créditos para a ideia de usar o LinearSVC dessa maneira vão para o Karpathy, minha mudança foi apenas usar o classificador sobre os embeddings.

## Licença

Licença MIT
