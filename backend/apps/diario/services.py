class DiarioIAService:

    @staticmethod
    def gerar_resumo(conteudo):

        palavras = conteudo.split()

        resumo = " ".join(palavras[:30])

        return f"""
        Aula registrada automaticamente pela IA.

        Resumo:
        {resumo}...
        """