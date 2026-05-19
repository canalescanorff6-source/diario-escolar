from django.db import models
from django.conf import settings
from django.utils import timezone


# =====================================================
# ANO LETIVO
# =====================================================

class AnoLetivo(models.Model):

    ano = models.IntegerField(unique=True)

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-ano']

    def __str__(self):
        return str(self.ano)


# =====================================================
# DISCIPLINAS
# =====================================================

class Disciplina(models.Model):

    nome = models.CharField(max_length=100, unique=True)

    cor = models.CharField(
        max_length=20,
        default="#5eead4"
    )

    criada_em = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nome


# =====================================================
# TURMAS
# =====================================================

class Turma(models.Model):

    nome = models.CharField(max_length=100)

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.CASCADE
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        limit_choices_to={'tipo': 'PROF'}
    )

    sala = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    turno = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    ativa = models.BooleanField(default=True)

    criada_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return f"{self.nome} - {self.ano_letivo}"


# =====================================================
# ALUNOS
# =====================================================

class Aluno(models.Model):

    nome = models.CharField(max_length=150)

    matricula = models.CharField(
        max_length=50,
        unique=True
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="alunos"
    )

    data_nascimento = models.DateField(
        blank=True,
        null=True
    )

    responsavel = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    telefone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    # NOVO
    foto = models.ImageField(
        upload_to='alunos/',
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['nome']

    def __str__(self):
        return self.nome


# =====================================================
# NOTAS
# =====================================================

class Nota(models.Model):

    BIMESTRES = (
        (1, "1º Bimestre"),
        (2, "2º Bimestre"),
        (3, "3º Bimestre"),
        (4, "4º Bimestre"),
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    bimestre = models.IntegerField(
        choices=BIMESTRES
    )

    # Nota final/média do bimestre.
    # Fica nula enquanto as três avaliações não forem preenchidas.
    valor = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    nota1 = models.DecimalField(
        "Nota 1",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    nota2 = models.DecimalField(
        "Nota 2",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    nota3 = models.DecimalField(
        "Nota 3",
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:

        unique_together = (
            'aluno',
            'disciplina',
            'bimestre'
        )

    @property
    def completa(self):
        return (
            self.nota1 is not None and
            self.nota2 is not None and
            self.nota3 is not None
        )

    def calcular_media(self):
        if not self.completa:
            return None

        return round(
            (self.nota1 + self.nota2 + self.nota3) / 3,
            2
        )

    def save(self, *args, **kwargs):
        self.valor = self.calcular_media()
        super().save(*args, **kwargs)

    def __str__(self):

        media = self.valor if self.valor is not None else "incompleta"

        return (
            f"{self.aluno.nome} - "
            f"{self.disciplina.nome} - "
            f"{self.get_bimestre_display()} - "
            f"{media}"
        )


# =====================================================
# FREQUÊNCIA
# =====================================================

class Frequencia(models.Model):

    STATUS_FREQUENCIA_CHOICES = (
        ("P", "Presença"),
        ("F", "Falta"),
        ("FJ", "Falta justificada"),
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE
    )

    # NOVO
    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        null=True,
        blank=True
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE
    )

    data = models.DateField()

    presente = models.BooleanField(default=True)

    status = models.CharField(
        max_length=2,
        choices=STATUS_FREQUENCIA_CHOICES,
        default="P",
        db_index=True,
        help_text="Status oficial do Diário Escolar: P, F ou FJ.",
    )

    observacao = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:

        ordering = ['-data']

        unique_together = (
            'aluno',
            'disciplina',
            'data'
        )

    def save(self, *args, **kwargs):
        if self.status == "P":
            self.presente = True
        elif self.status in ("F", "FJ"):
            self.presente = False
            if self.status == "FJ" and not self.observacao:
                self.observacao = "Falta justificada"
        super().save(*args, **kwargs)

    @property
    def status_oficial(self):
        if self.status:
            return self.status
        observacao = (self.observacao or "").lower()
        if "justificada" in observacao or "fj" in observacao:
            return "FJ"
        return "P" if self.presente else "F"

    def __str__(self):

        return (
            f"{self.aluno.nome} - "
            f"{self.get_status_display() if self.status else ('Presente' if self.presente else 'Falta')}"
        )


# =====================================================
# CONTEÚDO DA AULA
# =====================================================

class ConteudoAula(models.Model):

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )

    data = models.DateField()

    descricao = models.TextField()

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.turma.nome} - {self.data}"


# =====================================================
# ALERTAS IA
# =====================================================

class AlertaIA(models.Model):

    NIVEIS = (
        ("BAIXO", "Baixo"),
        ("MEDIO", "Médio"),
        ("ALTO", "Alto"),
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE
    )

    titulo = models.CharField(max_length=200)

    descricao = models.TextField()

    nivel = models.CharField(
        max_length=20,
        choices=NIVEIS
    )

    resolvido = models.BooleanField(default=False)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-criado_em']

    def __str__(self):
        return f"{self.aluno.nome} - {self.nivel}"

# =====================================================
# GESTÃO ESCOLAR — BASE ADMINISTRATIVA
# Mantém os models antigos e adiciona a estrutura do diário escolar.
# =====================================================

class Escola(models.Model):

    nome = models.CharField(max_length=180)

    aldeia = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    terra_indigena = models.CharField(
        "Terra indígena",
        max_length=120,
        blank=True,
        null=True
    )

    brasao_logo = models.ImageField(
        "Foto, logo ou brasão",
        upload_to="escolas/",
        blank=True,
        null=True,
        help_text="Imagem institucional exibida na tela de login institucional."
    )

    estado_nome = models.CharField(
        "Estado/órgão superior",
        max_length=160,
        default="ESTADO DO MARANHÃO",
        blank=True
    )

    secretaria = models.CharField(
        "Secretaria/órgão responsável",
        max_length=180,
        default="SECRETARIA DE ESTADO DA EDUCAÇÃO",
        blank=True
    )

    gestor_nome = models.CharField(
        "Diretor(a) ou gestor(a)",
        max_length=180,
        blank=True,
        null=True
    )

    gestor_cargo = models.CharField(
        "Cargo da gestão",
        max_length=120,
        default="Direção escolar",
        blank=True
    )

    texto_institucional = models.TextField(
        "Texto institucional do login",
        blank=True,
        null=True
    )

    municipio = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    estado = models.CharField(
        max_length=2,
        default="MA"
    )

    ano_letivo_ativo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="escolas_ativas"
    )

    ativa = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["nome"]
        verbose_name = "Escola"
        verbose_name_plural = "Escolas"

    def __str__(self):
        return self.nome


class ProfessorPerfil(models.Model):

    usuario = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="perfil_professor",
        limit_choices_to={"tipo": "PROF"}
    )

    # Campo legado para compatibilidade com bancos antigos que tinham professor_id obrigatório.
    # O campo oficial do sistema é usuario; este campo apenas evita quebra em bases antigas.
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="+",
        db_column="professor_id",
        limit_choices_to={"tipo": "PROF"}
    )

    escola = models.ForeignKey(
        Escola,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="professores"
    )

    telefone = models.CharField(
        max_length=30,
        blank=True,
        null=True
    )

    formacao = models.CharField(
        max_length=150,
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["usuario__first_name", "usuario__username"]
        verbose_name = "Perfil do professor"
        verbose_name_plural = "Perfis dos professores"

    def save(self, *args, **kwargs):
        if self.usuario_id and not self.professor_id:
            self.professor_id = self.usuario_id
        super().save(*args, **kwargs)

    def __str__(self):
        nome = self.usuario.get_full_name() or self.usuario.username
        return nome


class ProfessorTurmaDisciplina(models.Model):

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="vinculos_pedagogicos",
        limit_choices_to={"tipo": "PROF"}
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="vinculos_professores"
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name="vinculos_professores"
    )

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["turma__nome", "disciplina__nome"]
        unique_together = (
            "professor",
            "turma",
            "disciplina",
            "ano_letivo",
        )
        verbose_name = "Vínculo professor/turma/disciplina"
        verbose_name_plural = "Vínculos professor/turma/disciplina"

    def __str__(self):
        nome = self.professor.get_full_name() or self.professor.username
        return f"{nome} • {self.turma.nome} • {self.disciplina.nome}"


class HorarioAula(models.Model):

    DIAS_SEMANA = (
        (1, "2ª Feira"),
        (2, "3ª Feira"),
        (3, "4ª Feira"),
        (4, "5ª Feira"),
        (5, "6ª Feira"),
        (6, "Sábado"),
    )

    TURNO_CHOICES = (
        ("MATUTINO", "Matutino"),
        ("VESPERTINO", "Vespertino"),
        ("NOTURNO", "Noturno"),
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="horarios_aula",
        limit_choices_to={"tipo": "PROF"}
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="horarios"
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name="horarios"
    )

    dia_semana = models.PositiveSmallIntegerField(choices=DIAS_SEMANA)

    ordem = models.PositiveSmallIntegerField(
        "Horário",
        default=1,
        help_text="Exemplo: 1 para 1º horário, 2 para 2º horário."
    )

    # Compatibilidade com bancos antigos que tinham este campo obrigatório.
    # Mantém o sistema funcionando sem quebrar a grade semanal.
    horario_numero = models.PositiveSmallIntegerField(
        "Número do horário",
        default=1
    )

    hora_inicio = models.TimeField()

    hora_fim = models.TimeField()

    turno = models.CharField(
        max_length=20,
        choices=TURNO_CHOICES,
        blank=True,
        null=True
    )

    ativo = models.BooleanField(default=True)

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["dia_semana", "ordem", "hora_inicio"]
        unique_together = (
            "professor",
            "turma",
            "disciplina",
            "dia_semana",
            "ordem",
        )
        verbose_name = "Horário de aula"
        verbose_name_plural = "Horários de aula"

    def save(self, *args, **kwargs):
        if not self.horario_numero:
            self.horario_numero = self.ordem or 1
        if not self.ordem:
            self.ordem = self.horario_numero or 1
        super().save(*args, **kwargs)

    def __str__(self):
        return (
            f"{self.get_dia_semana_display()} • {self.ordem}º • "
            f"{self.turma.nome} • {self.disciplina.nome}"
        )

# =====================================================
# ETAPA 9 — CALENDÁRIO, FECHAMENTO, PARECER E ASSINATURA
# Models aditivos para gestão escolar sem remover estrutura existente.
# =====================================================

class CalendarioEvento(models.Model):

    TIPOS = (
        ("AULA", "Dia letivo"),
        ("FERIADO", "Feriado"),
        ("REUNIAO", "Reunião"),
        ("AVALIACAO", "Avaliação"),
        ("PLANEJAMENTO", "Planejamento"),
        ("EVENTO", "Evento escolar"),
    )

    escola = models.ForeignKey(
        Escola,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_calendario"
    )

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="eventos_calendario"
    )

    titulo = models.CharField(max_length=180)

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS,
        default="EVENTO"
    )

    data_inicio = models.DateField()

    data_fim = models.DateField(
        null=True,
        blank=True
    )

    descricao = models.TextField(
        blank=True,
        null=True
    )

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["data_inicio", "titulo"]
        verbose_name = "Evento do calendário escolar"
        verbose_name_plural = "Eventos do calendário escolar"

    def __str__(self):
        return f"{self.data_inicio} • {self.titulo}"


class FechamentoBimestre(models.Model):

    BIMESTRES = Nota.BIMESTRES

    STATUS = (
        ("ABERTO", "Aberto"),
        ("FECHADO", "Fechado"),
        ("REABERTO", "Reaberto"),
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="fechamentos_bimestrais"
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_bimestrais"
    )

    bimestre = models.IntegerField(choices=BIMESTRES)

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="ABERTO"
    )

    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_realizados"
    )

    fechado_em = models.DateTimeField(
        null=True,
        blank=True
    )

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["turma__nome", "bimestre", "disciplina__nome"]
        unique_together = ("turma", "disciplina", "bimestre")
        verbose_name = "Fechamento bimestral"
        verbose_name_plural = "Fechamentos bimestrais"

    def __str__(self):
        disc = self.disciplina.nome if self.disciplina else "Geral"
        return f"{self.turma.nome} • {disc} • {self.get_bimestre_display()} • {self.status}"


class ParecerAluno(models.Model):

    BIMESTRES = Nota.BIMESTRES

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name="pareceres"
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="pareceres_alunos"
    )

    bimestre = models.IntegerField(
        choices=BIMESTRES,
        null=True,
        blank=True
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="pareceres_professor"
    )

    texto = models.TextField()

    encaminhamentos = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Parecer descritivo do aluno"
        verbose_name_plural = "Pareceres descritivos dos alunos"

    def __str__(self):
        periodo = self.get_bimestre_display() if self.bimestre else "Geral"
        return f"{self.aluno.nome} • {periodo}"


class AssinaturaDocumento(models.Model):

    TIPOS = (
        ("DIARIO", "Diário de classe"),
        ("BOLETIM", "Boletim"),
        ("FREQUENCIA", "Frequência"),
        ("PARECER", "Parecer"),
        ("RELATORIO", "Relatório"),
    )

    tipo = models.CharField(
        max_length=20,
        choices=TIPOS
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assinaturas_documentos"
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="assinaturas_documentos"
    )

    assinado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_assinados"
    )

    cargo = models.CharField(
        max_length=120,
        blank=True,
        null=True
    )

    observacoes = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Assinatura de documento"
        verbose_name_plural = "Assinaturas de documentos"

    def __str__(self):
        nome = self.assinado_por.get_full_name() if self.assinado_por else "Sem usuário"
        return f"{self.get_tipo_display()} • {nome}"



# =====================================================
# ETAPA 10 — HISTÓRICO, AUDITORIA, DOCUMENTOS E NOTIFICAÇÕES
# Models aditivos para gestão escolar avançada.
# =====================================================

class HistoricoAluno(models.Model):

    SITUACOES = (
        ("MATRICULA", "Matrícula"),
        ("TRANSFERENCIA", "Transferência"),
        ("EVASAO", "Evasão"),
        ("RETORNO", "Retorno"),
        ("APROVACAO", "Aprovação"),
        ("REPROVACAO", "Reprovação"),
        ("OBSERVACAO", "Observação pedagógica"),
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.CASCADE,
        related_name="historicos"
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_alunos"
    )

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_alunos"
    )

    situacao = models.CharField(
        max_length=30,
        choices=SITUACOES,
        default="OBSERVACAO"
    )

    data = models.DateField(default=timezone.now)

    descricao = models.TextField()

    registrado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="historicos_registrados"
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-data", "-criado_em"]
        verbose_name = "Histórico do aluno"
        verbose_name_plural = "Históricos dos alunos"

    def __str__(self):
        return f"{self.aluno.nome} • {self.get_situacao_display()} • {self.data}"


class AuditoriaSistema(models.Model):

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="auditorias"
    )

    modulo = models.CharField(max_length=120)

    acao = models.CharField(max_length=160)

    objeto = models.CharField(
        max_length=180,
        blank=True,
        null=True
    )

    descricao = models.TextField(
        blank=True,
        null=True
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Auditoria do sistema"
        verbose_name_plural = "Auditorias do sistema"

    def __str__(self):
        nome = self.usuario.get_full_name() if self.usuario else "Sistema"
        return f"{self.criado_em:%d/%m/%Y %H:%M} • {nome} • {self.acao}"


class DocumentoGerado(models.Model):

    TIPOS = (
        ("DIARIO", "Diário de classe"),
        ("BOLETIM", "Boletim"),
        ("FREQUENCIA", "Frequência"),
        ("PARECER", "Parecer"),
        ("RELATORIO", "Relatório"),
        ("OUTRO", "Outro documento"),
    )

    STATUS = (
        ("GERADO", "Gerado"),
        ("IMPRESSO", "Impresso"),
        ("ASSINADO", "Assinado"),
        ("ARQUIVADO", "Arquivado"),
    )

    tipo = models.CharField(max_length=20, choices=TIPOS)

    titulo = models.CharField(max_length=180)

    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_gerados"
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_gerados"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS,
        default="GERADO"
    )

    observacoes = models.TextField(blank=True, null=True)

    gerado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="documentos_gerados"
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-criado_em"]
        verbose_name = "Documento gerado"
        verbose_name_plural = "Documentos gerados"

    def __str__(self):
        return f"{self.get_tipo_display()} • {self.titulo}"


class NotificacaoGestao(models.Model):

    NIVEIS = (
        ("INFO", "Informação"),
        ("ATENCAO", "Atenção"),
        ("CRITICO", "Crítico"),
        ("SUCESSO", "Sucesso"),
    )

    titulo = models.CharField(max_length=180)

    mensagem = models.TextField()

    nivel = models.CharField(
        max_length=20,
        choices=NIVEIS,
        default="INFO"
    )

    destino = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="notificacoes_gestao"
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificacoes_gestao"
    )

    aluno = models.ForeignKey(
        Aluno,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificacoes_gestao"
    )

    resolvida = models.BooleanField(default=False)

    criado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="notificacoes_criadas"
    )

    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["resolvida", "-criado_em"]
        verbose_name = "Notificação da gestão"
        verbose_name_plural = "Notificações da gestão"

    def __str__(self):
        return f"{self.get_nivel_display()} • {self.titulo}"


# =====================================================
# ETAPA 11 — Gestão executiva, backup e integrações
# =====================================================

class BackupSistema(models.Model):
    STATUS_CHOICES = (
        ("GERADO", "Gerado"),
        ("FALHA", "Falha"),
    )

    titulo = models.CharField(max_length=120)
    arquivo = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="GERADO")
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        "usuarios.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="backups_sistema"
    )

    class Meta:
        verbose_name = "Backup do Sistema"
        verbose_name_plural = "Backups do Sistema"
        ordering = ["-criado_em"]

    def __str__(self):
        return self.titulo


class IntegracaoEscolar(models.Model):
    TIPO_CHOICES = (
        ("GESTAO", "Cadastro pela gestão"),
        ("PDF", "PDF/documento"),
        ("SISTEMA", "Sistema externo"),
        ("OUTRO", "Outro"),
    )

    nome = models.CharField(max_length=120)
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default="GESTAO")
    descricao = models.TextField(blank=True, null=True)
    ativa = models.BooleanField(default=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Integração Escolar"
        verbose_name_plural = "Integrações Escolares"
        ordering = ["nome"]

    def __str__(self):
        return self.nome


class IndicadorGestao(models.Model):
    nome = models.CharField(max_length=120)
    valor = models.CharField(max_length=80)
    descricao = models.TextField(blank=True, null=True)
    referencia = models.DateField(blank=True, null=True)
    criado_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Indicador de Gestão"
        verbose_name_plural = "Indicadores de Gestão"
        ordering = ["nome"]

    def __str__(self):
        return f"{self.nome}: {self.valor}"


# =====================================================
# FECHAMENTO MENSAL OFICIAL — ETAPA 1221-1280
# Estrutura persistente para fechar mês por professor/turma/disciplina.
# =====================================================
class FechamentoMensal(models.Model):
    STATUS = (
        ("ABERTO", "Aberto"),
        ("PENDENTE", "Pendente"),
        ("FECHADO", "Fechado"),
        ("REABERTO", "Reaberto"),
    )

    ano_letivo = models.ForeignKey(
        AnoLetivo,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_mensais",
    )

    turma = models.ForeignKey(
        Turma,
        on_delete=models.CASCADE,
        related_name="fechamentos_mensais",
    )

    disciplina = models.ForeignKey(
        Disciplina,
        on_delete=models.CASCADE,
        related_name="fechamentos_mensais",
    )

    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="fechamentos_mensais",
        limit_choices_to={"tipo": "PROF"},
    )

    mes = models.PositiveSmallIntegerField()
    ano = models.PositiveSmallIntegerField(default=timezone.now().year)

    aulas_previstas = models.PositiveSmallIntegerField(default=0)
    aulas_dadas = models.PositiveSmallIntegerField(default=0)
    frequencias_lancadas = models.PositiveIntegerField(default=0)
    conteudos_registrados = models.PositiveIntegerField(default=0)
    percentual_frequencia = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    status = models.CharField(max_length=20, choices=STATUS, default="ABERTO")
    pendencias = models.TextField(blank=True, null=True)
    observacoes = models.TextField(blank=True, null=True)

    fechado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="fechamentos_mensais_realizados",
    )
    fechado_em = models.DateTimeField(null=True, blank=True)

    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-ano", "-mes", "turma__nome", "disciplina__nome"]
        unique_together = ("turma", "disciplina", "professor", "mes", "ano")
        verbose_name = "Fechamento mensal oficial"
        verbose_name_plural = "Fechamentos mensais oficiais"

    def fechar(self, usuario=None):
        self.status = "FECHADO"
        self.fechado_por = usuario
        self.fechado_em = timezone.now()
        self.save(update_fields=["status", "fechado_por", "fechado_em", "atualizado_em"])

    def __str__(self):
        return f"{self.turma.nome} • {self.disciplina.nome} • {self.mes:02d}/{self.ano} • {self.status}"
