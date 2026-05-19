from django.db.models import Avg, Count, Q

from apps.academico.models import (
    Nota,
    Frequencia,
)


class AnaliseInteligenteService:

    # ================================
    # 📊 RESUMO GERAL DA TURMA
    # ================================
    @staticmethod
    def resumo_turma(turma):

        media_geral = Nota.objects.filter(
            aluno__turma=turma
        ).aggregate(
            media=Avg("valor")
        )["media"] or 0

        total_alunos = turma.alunos.count()

        total_aulas = Frequencia.objects.filter(
            aluno__turma=turma
        ).count()

        total_faltas = Frequencia.objects.filter(
            aluno__turma=turma,
            presente=False
        ).count()

        percentual_presenca = 0

        if total_aulas > 0:

            percentual_presenca = round(
                ((total_aulas - total_faltas) / total_aulas) * 100,
                2
            )

        return {

            "media_geral": round(media_geral, 2),

            "total_alunos": total_alunos,

            "total_faltas": total_faltas,

            "percentual_presenca": percentual_presenca,

        }

    # ================================
    # 🚨 ALUNOS EM RISCO
    # ================================
    @staticmethod
    def alunos_em_risco(turma):

        alunos = turma.alunos.all()

        alunos_risco = []

        for aluno in alunos:

            media = Nota.objects.filter(
                aluno=aluno
            ).aggregate(
                media=Avg("valor")
            )["media"] or 0

            total_aulas = Frequencia.objects.filter(
                aluno=aluno
            ).count()

            faltas = Frequencia.objects.filter(
                aluno=aluno,
                presente=False
            ).count()

            percentual_presenca = 100

            if total_aulas > 0:

                percentual_presenca = round(
                    ((total_aulas - faltas) / total_aulas) * 100,
                    2
                )

            risco = AnaliseInteligenteService.calcular_risco(
                media,
                percentual_presenca
            )

            if risco in ["MÉDIO", "ALTO"]:

                alunos_risco.append({

                    "nome": aluno.nome,

                    "media": round(media, 2),

                    "faltas": faltas,

                    "presenca_%": percentual_presenca,

                    "status": AnaliseInteligenteService.status_final(
                        media,
                        percentual_presenca
                    ),

                    "nivel_risco": risco

                })

        return alunos_risco

    # ================================
    # 🧠 SCORE INTELIGENTE
    # ================================
    @staticmethod
    def calcular_risco(media, presenca_percentual):

        score = 0

        # Peso maior para média

        if media < 5:

            score += 3

        elif media < 6:

            score += 2

        elif media < 7:

            score += 1

        # Peso presença

        if presenca_percentual < 60:

            score += 3

        elif presenca_percentual < 75:

            score += 2

        elif presenca_percentual < 85:

            score += 1

        if score >= 5:

            return "ALTO"

        elif score >= 3:

            return "MÉDIO"

        else:

            return "BAIXO"

    # ================================
    # 🎓 STATUS FINAL DO ALUNO
    # ================================
    @staticmethod
    def status_final(media, presenca_percentual):

        if media >= 7 and presenca_percentual >= 75:

            return "APROVADO"

        elif media >= 5:

            return "RECUPERAÇÃO"

        else:

            return "REPROVADO"