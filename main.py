import argparse


def main():
    parser = argparse.ArgumentParser(description="RAG CLI - Deporte municipal")
    parser.add_argument("--index", action="store_true", help="Indexar el corpus")
    parser.add_argument("--query", type=str, help="Solo retrieval: mostrar chunks recuperados")
    parser.add_argument("--ask", type=str, help="Pregunta RAG completa (retrieval + generación)")
    parser.add_argument("--k", type=int, default=None, help="Override de TOP_K")

    args = parser.parse_args()

    if args.index:
        print("TODO: indexar corpus")
    elif args.query:
        print(f"TODO: retrieval para: {args.query}")
    elif args.ask:
        print(f"TODO: RAG completo para: {args.ask}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
