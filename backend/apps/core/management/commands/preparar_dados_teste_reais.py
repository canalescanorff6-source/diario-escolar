from datetime import date, time, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.academico.models import (
    Aluno,
    AnoLetivo,
    ConteudoAula,
    Disciplina,
    Escola,
    FechamentoMensal,
    Frequencia,
    HorarioAula,
    Nota,
    ProfessorPerfil,
    ProfessorTurmaDisciplina,
    Turma,
)
from apps.diario.models import Diario


class Command(BaseCommand):
    help = "Cria dados oficiais pela gestão para validar diário de classe completo, sem Excel/importador antigo."

    def add_arguments(self, parser):
        parser.add_argument("--usuarios", action="store_true", help="Mostra usuários e senhas criados/atualizados.")

    def _usuario(self, username, tipo, first_name, last_name, senha, staff=False):
        User = get_user_model()
        user, _ = User.objects.get_or_create(
            username=username,
            defaults={"tipo": tipo, "first_name": first_name, "last_name": last_name},
        )
        user.tipo = tipo
        user.first_name = first_name
        user.last_name = last_name
        user.is_staff = bool(staff)
        user.set_password(senha)
        user.save()
        return user

    def handle(self, *args, **options):
        ano_atual = date.today().year
        ano_letivo, _ = AnoLetivo.objects.update_or_create(ano=ano_atual, defaults={"ativo": True})

        escola, _ = Escola.objects.update_or_create(
            nome="Centro de Educação Escolar Indígena Januária",
            defaults={
                "aldeia": "Januária",
                "terra_indigena": "Rio Pindaré",
                "municipio": "Abaetetuba",
                "estado": "MA",
                "estado_nome": "ESTADO DO MARANHÃO",
                "secretaria": "SECRETARIA DE ESTADO DA EDUCAÇÃO",
                "gestor_nome": "Direção escolar",
                "gestor_cargo": "Direção escolar",
                "texto_institucional": "Portal institucional de acesso ao diário escolar da instituição.",
                "ano_letivo_ativo": ano_letivo,
                "ativa": True,
            },
        )

        gestor = self._usuario("gestao_teste", "ADMIN", "Gestão", "Teste", "gestao123", staff=True)
        professor_teste = self._usuario("professor_teste", "PROF", "Professor", "Teste", "professor123")
        professor_manha = self._usuario("professor_manha", "PROF", "Professor", "Matutino", "professor123")
        professor_tarde = self._usuario("professor_tarde", "PROF", "Professor", "Vespertino", "professor123")
        professor_noite = self._usuario("professor_noite", "PROF", "Professor", "EJA", "professor123")

        for professor, formacao in [
            (professor_teste, "Licenciatura — Turmas vespertinas"),
            (professor_manha, "Pedagogia — Anos iniciais"),
            (professor_tarde, "Licenciatura — Fundamental II e Médio"),
            (professor_noite, "Educação de Jovens e Adultos"),
        ]:
            ProfessorPerfil.objects.update_or_create(
                usuario=professor,
                defaults={
                    "professor": professor,
                    "escola": escola,
                    "telefone": "(91) 99999-0000",
                    "formacao": formacao,
                    "ativo": True,
                },
            )

        disciplinas_base = [
            ("Língua Portuguesa", "#5eead4"),
            ("Matemática", "#38bdf8"),
            ("Ciências", "#a78bfa"),
            ("História", "#facc15"),
            ("Geografia", "#34d399"),
            ("Arte", "#fb7185"),
            ("Educação Física", "#f97316"),
            ("Inglês", "#818cf8"),
        ]
        disciplinas = []
        for nome, cor in disciplinas_base:
            disciplina, _ = Disciplina.objects.update_or_create(nome=nome, defaults={"cor": cor})
            disciplinas.append(disciplina)

        turmas_config = [
            ("1º Ano A — Matutino", "MATUTINO", "Sala M1", professor_manha, disciplinas[:3]),
            ("2º Ano A — Matutino", "MATUTINO", "Sala M2", professor_manha, disciplinas[1:4]),
            ("3º Ano A — Matutino", "MATUTINO", "Sala M3", professor_manha, disciplinas[2:5]),
            ("4º Ano A — Matutino", "MATUTINO", "Sala M4", professor_manha, [disciplinas[0], disciplinas[4], disciplinas[5]]),
            ("5º Ano A — Matutino", "MATUTINO", "Sala M5", professor_manha, [disciplinas[0], disciplinas[1], disciplinas[4]]),
            ("6º Ano A — Vespertino", "VESPERTINO", "Sala V1", professor_teste, [disciplinas[0], disciplinas[1], disciplinas[2]]),
            ("7º Ano A — Vespertino", "VESPERTINO", "Sala V2", professor_tarde, [disciplinas[0], disciplinas[1], disciplinas[3]]),
            ("8º Ano A — Vespertino", "VESPERTINO", "Sala V3", professor_tarde, [disciplinas[1], disciplinas[2], disciplinas[4]]),
            ("9º Ano A — Vespertino", "VESPERTINO", "Sala V4", professor_tarde, [disciplinas[0], disciplinas[3], disciplinas[4]]),
            ("1ª Série EM — Vespertino", "VESPERTINO", "Sala V5", professor_tarde, [disciplinas[0], disciplinas[1], disciplinas[7]]),
            ("2ª Série EM — Vespertino", "VESPERTINO", "Sala V6", professor_tarde, [disciplinas[1], disciplinas[2], disciplinas[7]]),
            ("3ª Série EM — Vespertino", "VESPERTINO", "Sala V7", professor_tarde, [disciplinas[0], disciplinas[1], disciplinas[3]]),
            ("6º Ano B — Vespertino", "VESPERTINO", "Sala V8", professor_tarde, [disciplinas[0], disciplinas[1], disciplinas[5]]),
            ("EJA I — Noturno", "NOTURNO", "Sala N1", professor_noite, [disciplinas[0], disciplinas[1], disciplinas[3]]),
            ("EJA II — Noturno", "NOTURNO", "Sala N2", professor_noite, [disciplinas[0], disciplinas[1], disciplinas[4]]),
            ("EJA III — Noturno", "NOTURNO", "Sala N3", professor_noite, [disciplinas[0], disciplinas[2], disciplinas[4]]),
            ("EJA IV — Noturno", "NOTURNO", "Sala N4", professor_noite, [disciplinas[1], disciplinas[3], disciplinas[7]]),
            ("EJA V — Noturno", "NOTURNO", "Sala N5", professor_noite, [disciplinas[0], disciplinas[1], disciplinas[7]]),
        ]

        horarios_por_turno = {
            "MATUTINO": [(1, time(7, 30), time(8, 20)), (2, time(8, 20), time(9, 10))],
            "VESPERTINO": [(1, time(13, 30), time(14, 20)), (2, time(14, 20), time(15, 10))],
            "NOTURNO": [(1, time(19, 0), time(19, 45)), (2, time(19, 45), time(20, 30))],
        }

        hoje = date.today()
        inicio_mes = hoje.replace(day=1)
        dias_letivos = [inicio_mes + timedelta(days=i) for i in range(0, min(15, max(hoje.day, 3))) if (inicio_mes + timedelta(days=i)).weekday() < 5]
        if len(dias_letivos) < 3:
            dias_letivos = [hoje - timedelta(days=i) for i in range(3) if (hoje - timedelta(days=i)).weekday() < 5] or [hoje]

        turmas_criadas = []
        total_horarios = 0
        total_alunos_criados = 0

        for idx_turma, (nome, turno, sala, professor, disciplinas_turma) in enumerate(turmas_config, start=1):
            turma, _ = Turma.objects.update_or_create(
                nome=nome,
                ano_letivo=ano_letivo,
                defaults={"professor": professor, "sala": sala, "turno": turno, "ativa": True},
            )
            turmas_criadas.append(turma)

            for disciplina in disciplinas_turma:
                ProfessorTurmaDisciplina.objects.update_or_create(
                    professor=professor,
                    turma=turma,
                    disciplina=disciplina,
                    ano_letivo=ano_letivo,
                    defaults={"ativo": True},
                )

            for i in range(1, 9):
                aluno, _ = Aluno.objects.update_or_create(
                    matricula=f"DIA-{ano_atual}-{idx_turma:02d}-{i:03d}",
                    defaults={
                        "nome": f"Aluno {nome.split('—')[0].strip()} {i:02d}",
                        "turma": turma,
                        "responsavel": f"Responsável {idx_turma:02d}-{i:02d}",
                        "telefone": f"(91) 98888-{idx_turma:02d}{i:02d}",
                        "ativo": True,
                    },
                )
                total_alunos_criados += 1

            for dia in range(1, 6):
                for ordem, inicio, fim in horarios_por_turno[turno]:
                    disciplina = disciplinas_turma[(dia + ordem - 2) % len(disciplinas_turma)]
                    HorarioAula.objects.update_or_create(
                        professor=professor,
                        turma=turma,
                        dia_semana=dia,
                        horario_numero=ordem,
                        defaults={
                            "disciplina": disciplina,
                            "ordem": ordem,
                            "hora_inicio": inicio,
                            "hora_fim": fim,
                            "turno": turno,
                            "ativo": True,
                        },
                    )
                    total_horarios += 1

            alunos_turma = list(turma.alunos.filter(ativo=True).order_by("nome")[:8])
            for data_aula in dias_letivos[:5]:
                for disciplina in disciplinas_turma:
                    for idx, aluno in enumerate(alunos_turma):
                        status = "P"
                        obs = ""
                        if idx == 2 and data_aula.day % 3 == 0:
                            status, obs = "F", "Falta registrada pela gestão/teste oficial."
                        elif idx == 5 and data_aula.day % 4 == 0:
                            status, obs = "FJ", "Falta justificada registrada pela gestão/teste oficial."
                        Frequencia.objects.update_or_create(
                            aluno=aluno,
                            disciplina=disciplina,
                            data=data_aula,
                            defaults={"turma": turma, "status": status, "presente": status == "P", "observacao": obs},
                        )

                    ConteudoAula.objects.update_or_create(
                        turma=turma,
                        disciplina=disciplina,
                        professor=professor,
                        data=data_aula,
                        defaults={
                            "descricao": f"Aula oficial de {disciplina.nome}: desenvolvimento do conteúdo previsto, atividade orientada e correção coletiva.",
                            "observacoes": "Registro criado pela gestão para validar Diário de Classe Oficial completo.",
                        },
                    )

                    Diario.objects.update_or_create(
                        turma=turma,
                        professor=professor,
                        data=data_aula,
                        disciplina=disciplina.nome,
                        defaults={
                            "titulo": f"Diário oficial — {disciplina.nome}",
                            "bimestre": 1,
                            "quantidade_aulas": 1,
                            "conteudo": f"Registro mensal de aula de {disciplina.nome} com frequência P/F/FJ e conteúdo oficial.",
                            "objetivos": "Garantir aprendizagem e consolidar frequência mensal.",
                            "habilidades": "Participação, leitura, escrita, resolução de problemas e acompanhamento contínuo.",
                            "metodologia": "Aula dialogada, atividade prática e acompanhamento individual.",
                            "recursos": "Quadro, caderno, material didático e sistema Diário IA.",
                            "avaliacao": "Participação, exercício e frequência lançada.",
                            "status": "CONCLUIDA",
                            "resumo_ia": "Registro suficiente para IA pedagógica, diário oficial e fechamento mensal.",
                        },
                    )

            for aluno in alunos_turma[:4]:
                for disciplina in disciplinas_turma[:2]:
                    Nota.objects.update_or_create(
                        aluno=aluno,
                        disciplina=disciplina,
                        bimestre=1,
                        defaults={"turma": turma, "nota1": Decimal("8.0"), "nota2": Decimal("7.5"), "nota3": Decimal("8.5")},
                    )

            for disciplina in disciplinas_turma:
                freq_total = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data__month=hoje.month, data__year=hoje.year).count()
                freq_presentes = Frequencia.objects.filter(turma=turma, disciplina=disciplina, data__month=hoje.month, data__year=hoje.year, status="P").count()
                conteudos = ConteudoAula.objects.filter(turma=turma, disciplina=disciplina, professor=professor, data__month=hoje.month, data__year=hoje.year).count()
                horarios_disc = HorarioAula.objects.filter(turma=turma, disciplina=disciplina, professor=professor, ativo=True).count()
                percentual = Decimal("0.00") if not freq_total else Decimal(freq_presentes * 100 / freq_total).quantize(Decimal("0.01"))
                FechamentoMensal.objects.update_or_create(
                    turma=turma,
                    disciplina=disciplina,
                    professor=professor,
                    mes=hoje.month,
                    ano=hoje.year,
                    defaults={
                        "ano_letivo": ano_letivo,
                        "aulas_previstas": max(horarios_disc * 4, conteudos),
                        "aulas_dadas": conteudos,
                        "frequencias_lancadas": freq_total,
                        "conteudos_registrados": conteudos,
                        "percentual_frequencia": percentual,
                        "status": "FECHADO" if conteudos and freq_total else "PENDENTE",
                        "pendencias": "Sem pendências críticas nos dados oficiais de teste." if conteudos and freq_total else "Completar frequência e conteúdo.",
                        "observacoes": "Fechamento mensal persistente criado sem Excel/importador.",
                        "fechado_por": gestor if conteudos and freq_total else None,
                        "fechado_em": timezone.now() if conteudos and freq_total else None,
                    },
                )

        self.stdout.write(self.style.SUCCESS("Dados oficiais de teste preparados pela gestão, sem Excel/importador."))
        self.stdout.write(f"Escola: {escola.nome}")
        self.stdout.write(f"Turmas oficiais: {len(turmas_criadas)} | Manhã=5 | Tarde=8 | Noite/EJA=5")
        self.stdout.write(f"Alunos gerados/atualizados: {total_alunos_criados} | Disciplinas: {len(disciplinas)} | Horários criados/atualizados: {total_horarios}")
        self.stdout.write(f"Frequências no mês: {Frequencia.objects.filter(data__month=hoje.month, data__year=hoje.year).count()}")
        self.stdout.write(f"Conteúdos no mês: {ConteudoAula.objects.filter(data__month=hoje.month, data__year=hoje.year).count()}")
        self.stdout.write(f"Diários no mês: {Diario.objects.filter(data__month=hoje.month, data__year=hoje.year).count()}")
        self.stdout.write(f"Fechamentos mensais: {FechamentoMensal.objects.filter(mes=hoje.month, ano=hoje.year).count()}")
        if options.get("usuarios"):
            self.stdout.write("Login gestão: gestao_teste / gestao123")
            self.stdout.write("Login professor principal: professor_teste / professor123")
            self.stdout.write("Demais professores: professor_manha/professor_tarde/professor_noite / professor123")
