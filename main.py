import argparse


def main():
    parser = argparse.ArgumentParser(description="RAG CLI - Deporte municipal")
    parser.add_argument("--index", action="store_true", help="Indexar el corpus")
    parser.add_argument("--query", type=str, help="Solo retrieval: mostrar chunks recuperados")
    parser.add_argument("--ask", type=str, help="Pregunta RAG completa (retrieval + generación)")
    parser.add_argument("--k", type=int, default=None, help="Override de TOP_K")

    args = parser.parse_args()

    if args.index:
        from src.load import cargar_documentos
        from src.chunk import fragmentar_documentos
        from src.embed import ejecutar_embeddings
        from src.index import construir_indice

        docs = cargar_documentos()
        chunks = fragmentar_documentos(docs)
        ejecutar_embeddings(chunks)
        construir_indice()

    elif args.query:
        from src.retrieve import retrieve
        from config import TOP_K

        k = args.k or TOP_K
        resultados = retrieve(args.query, k=k)
        for i, r in enumerate(resultados, 1):
            print(f"\n--- Chunk {i} (source: {r['source']}, score: {r['score']:.3f}) ---")
            print(r["text"][:300])

    elif args.ask:
        print(f"TODO: RAG completo para: {args.ask}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()