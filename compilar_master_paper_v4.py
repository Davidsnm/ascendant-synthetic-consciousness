"""
COMPILADOR MAESTRO DEL PAPER CIENTÍFICO: PROYECTO ASCENDANT v4.0 (AUDITADO)
Autor Único e Investigador Principal: David San Nicolás Montero (ORCID: 0009-0000-9977-007X)
Edición Definitiva: Incorporación de correcciones metodológicas, ANOVA RCBD de bloques de semilla,
auditoría de causas de muerte, trazabilidad de denominadores, prudencia mecanicista y hashes SHA-256.
"""

import os
import shutil
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle, KeepTogether, PageBreak
)
from reportlab.pdfgen import canvas

# =========================================================================
# RUTAS DE COMPILACIÓN Y PUBLICACIÓN
# =========================================================================
base_dir = r"c:\Users\Usuario\Documents\nuevos proyectos\Proyecto ascendant"
pdf_path = os.path.join(base_dir, "Proyecto_Ascendant_Master_Scientific_Paper_David_San_Nicolas.pdf")
pdf_v4_path = os.path.join(base_dir, "Master_Scientific_Paper_David_San_Nicolas_v4.pdf")
repo_pdf_path = os.path.join(base_dir, "github_paper_repository", "Proyecto_Ascendant_Master_Scientific_Paper_David_San_Nicolas.pdf")
downloads_pdf_1 = r"C:\Users\Usuario\Downloads\Proyecto_Ascendant_Master_Scientific_Paper_David_San_Nicolas.pdf"
downloads_pdf_2 = r"C:\Users\Usuario\Downloads\Master_Scientific_Paper_David_San_Nicolas.pdf"

class NumberedCanvas(canvas.Canvas):
    """
    Canvas de doble pasada para calcular el número total de páginas
    e insertar cabeceras y pies de página académicos rigurosos.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        print(f"TOTAL COMPILED PAGES: {num_pages}")
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_header_footer(num_pages)
            super().showPage()
        super().save()

    def draw_header_footer(self, page_count):
        self.saveState()
        self.setFont("Helvetica-Bold", 6.8)
        self.setFillColor(colors.HexColor('#4a5568'))

        # Running Header (Páginas > 1)
        if self._pageNumber > 1:
            self.drawString(36, 756, "PROJECT ASCENDANT: GROUNDED COMPUTATIONAL ANALOGS OF SYNTHETIC CONSCIOUSNESS")
            self.setFont("Helvetica", 6.8)
            self.drawRightString(letter[0] - 36, 756, "David San Nicolás Montero (2026)")
            self.setStrokeColor(colors.HexColor('#cbd5e0'))
            self.setLineWidth(0.6)
            self.line(36, 749, letter[0] - 36, 749)

        # Running Footer (Todas las páginas)
        self.setFont("Helvetica", 6.2)
        self.setFillColor(colors.HexColor('#718096'))
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(letter[0] - 36, 18, page_str)
        self.drawString(36, 18, "Project Ascendant v4.0 | Author: David San Nicolás Montero | Definitive Release DOI: 10.5281/zenodo.23990811 | Concept DOI: 10.5281/zenodo.23616626")
        self.setStrokeColor(colors.HexColor('#e2e8f0'))
        self.setLineWidth(0.5)
        self.line(36, 26, letter[0] - 36, 26)

        self.restoreState()


doc = SimpleDocTemplate(
    pdf_path,
    pagesize=letter,
    leftMargin=36,
    rightMargin=36,
    topMargin=40,
    bottomMargin=34
)

styles = getSampleStyleSheet()

# Tipografías y Jerarquías Visuales Optimizadas
title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontSize=12.5, leading=14.5, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'), alignment=1, spaceAfter=2.0)
subtitle_style = ParagraphStyle('SubTitleStyle', parent=styles['Normal'], fontSize=7.5, leading=9.5, fontName='Helvetica', textColor=colors.HexColor('#2b6cb0'), alignment=1, spaceAfter=2.5)
author_style = ParagraphStyle('AuthorStyle', parent=styles['Normal'], fontSize=7.2, leading=9.0, fontName='Helvetica-Bold', textColor=colors.HexColor('#2d3748'), alignment=1, spaceAfter=1.0)
affil_style = ParagraphStyle('AffilStyle', parent=styles['Normal'], fontSize=6.2, leading=8.0, fontName='Helvetica-Oblique', textColor=colors.HexColor('#4a5568'), alignment=1, spaceAfter=3.5)

abstract_style = ParagraphStyle('AbstractStyle', parent=styles['Normal'], fontSize=6.3, leading=8.2, fontName='Helvetica', textColor=colors.HexColor('#1a202c'), leftIndent=8, rightIndent=8, spaceAfter=3.0, alignment=4)
h1_style = ParagraphStyle('H1Style', parent=styles['Normal'], fontSize=8.2, leading=10.2, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'), spaceBefore=4.5, spaceAfter=2.0, keepWithNext=True)
h2_style = ParagraphStyle('H2Style', parent=styles['Normal'], fontSize=7.0, leading=8.8, fontName='Helvetica-Bold', textColor=colors.HexColor('#2c5282'), spaceBefore=3.0, spaceAfter=1.5, keepWithNext=True)
body_style = ParagraphStyle('BodyStyle', parent=styles['Normal'], fontSize=6.2, leading=8.0, fontName='Helvetica', textColor=colors.HexColor('#2d3748'), spaceAfter=2.5, alignment=4)
math_style = ParagraphStyle('MathStyle', parent=styles['Normal'], fontSize=6.0, leading=7.5, fontName='Courier', textColor=colors.HexColor('#742a2a'), leftIndent=6, rightIndent=6, spaceAfter=1.8)
bullet_style = ParagraphStyle('BulletStyle', parent=styles['Normal'], fontSize=6.0, leading=7.6, fontName='Helvetica', textColor=colors.HexColor('#2d3748'), leftIndent=8, firstLineIndent=-5, spaceAfter=1.5, alignment=4)
table_text = ParagraphStyle('TableText', parent=styles['Normal'], fontSize=5.3, leading=6.8, fontName='Helvetica', textColor=colors.HexColor('#1a202c'))
table_header = ParagraphStyle('TableHeader', parent=styles['Normal'], fontSize=5.6, leading=7.2, fontName='Helvetica-Bold', textColor=colors.HexColor('#1a365d'))

def R(*cells):
    return [Paragraph(c, table_text) for c in cells]

def HD(*cells):
    return [Paragraph('<b>%s</b>' % c, table_header) for c in cells]

def STY(t):
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'), ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 1.0), ('TOPPADDING', (0, 0), (-1, -1), 1.0),
        ('LEFTPADDING', (0, 0), (-1, -1), 2.0), ('RIGHTPADDING', (0, 0), (-1, -1), 2.0),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
        ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096'))]))
    return t

from reportlab.platypus import Image as RLImage
FIG_DIR = os.path.join(base_dir, 'experimeto generacional corregido', 'figuras_paper_v4')
caption_style = ParagraphStyle('Caption', parent=styles['Normal'], fontSize=5.8, leading=7.2, fontName='Helvetica-Oblique', textColor=colors.HexColor('#4a5568'), alignment=4, spaceAfter=3.0)

def FIG(fname, caption):
    img = RLImage(os.path.join(FIG_DIR, fname), width=540, height=540 * 825 / 2200.0)
    return KeepTogether([img, Paragraph(caption, caption_style)])

story = []

# =========================================================================
# CABECERA Y METADATOS ACADÉMICOS
# =========================================================================
story.append(Paragraph('PROJECT ASCENDANT: GROUNDED COMPUTATIONAL ANALOGS OF SYNTHETIC CONSCIOUSNESS', title_style))
story.append(Paragraph('EVALUATING MULTI-RATE ALLOSTASIS, FINITE AUTOBIOGRAPHICAL MEMORY, QUIESCENT PROSPECTION, AND INTERGENERATIONAL KNOWLEDGE TRANSMISSION ACROSS 38,620 SIMULATED AGENTS', subtitle_style))
story.append(Paragraph('<b>David San Nicolás Montero</b> &nbsp;|&nbsp; Lead Principal Investigator &amp; Sole Author', author_style))
story.append(Paragraph(
    'Independent Researcher | Project Ascendant<br/>'
    'ORCID: <font color="#2b6cb0"><u>0009-0000-9977-007X</u></font> &nbsp;|&nbsp; '
    'Definitive Release DOI: <font color="#2b6cb0"><u>10.5281/zenodo.23990811</u></font> &nbsp;|&nbsp; '
    'Concept DOI: <font color="#2b6cb0"><u>10.5281/zenodo.23616626</u></font><br/>'
    'Open Science Source &amp; Audited Database: <font color="#2b6cb0"><u>https://github.com/Davidsnm/ascendant-synthetic-consciousness</u></font>',
    affil_style
))
story.append(HRFlowable(width='100%', thickness=0.8, color=colors.HexColor('#2b6cb0'), spaceAfter=3))

# =========================================================================
# ABSTRACT
# =========================================================================
abstract_content = (
    '<b>Abstract</b>—Current artificial intelligence paradigms remain constrained by statistical token prediction in ungrounded latent spaces, devoid '
    'of somatic stakes, metabolic constraints, or existential imperatives (Harnad\'s Symbol Grounding Problem). '
    'In this work, we present <b>Project Ascendant v4.0</b>, an operational computational architecture conceived as an empirical stepping stone toward synthetic consciousness. '
    'Rather than asserting complete phenomenal sentience, Ascendant demonstrates an embodied autonomous entity driven by virtual homeostatic imperatives, '
    'capable of self-directed empirical learning, counterfactual reflection during resting windows, and intergenerational knowledge transmission. '
    'This updated edition presents the <b>new unified simulation engine</b> (Python/Node architecture, exact 4:1 relational integrity, and a strict -8 cycle/bite somatic wear invariant) '
    'and reports findings from the complete audited relational database (<b>9,655 runs, 38,620 agent biographies, and 539,201 episodic engrams</b> in SQLite). '
    'Statistical inference across 25,920 homogeneous offspring (&tau;<sub>0</sub> = 2,000 cycles) grouped across <i>G</i> = 360 independent seeds with cluster-robust sandwich standard errors '
    'establishes the exact causal hierarchy: congenital temperament retains an independent, statistically significant contribution to mortality '
    '(Wald<sub>cl</sub>(8 df) = 67.75, <i>p</i> = 1.38 &times; 10<sup>-11</sup>; McFadden &Delta;<i>R</i><sup>2</sup> = +0.0022), '
    'operating as a second-order behavioral modulator relative to first-order ecological pressures (predator density <i>K</i> = 5 and communal pantry access, &Delta;<i>R</i><sup>2</sup> = +0.0466). '
    'In a 2&times;2 factorial lineage benchmark (<i>N</i> = 1,440 runs across 360 matched seed blocks), a Randomized Complete Block Design (RCBD) ANOVA shows a large effect of communal pantry access '
    'on cumulative lineage longevity (<i>F</i>(1,1077) = 24.02, <i>p</i> = 1.1 &times; 10<sup>-6</sup>, &eta;<sub><i>p</i></sub><sup>2</sup> = 0.0218; paired +189.1 cycles, 95% CI [73.9, 304.3]; pooled over 8,640 runs <i>F</i>(1,6477) = 519.3, <i>p</i> &lt; 10<sup>-100</sup>, +423.5 cycles), '
    'whereas cultural transmission shows no detectable effect on raw longevity (<i>F</i> = 0.33, <i>p</i> = 0.564; pooled <i>p</i> = 0.370) and the interaction is null '
    '(<i>F</i> = 0.042, <i>p</i> = 0.839; paired 95% CI [-147.9, +117.7] cycles, within &plusmn;250 c equivalence). '
    'Competing risks survival analysis using Cox-Breslow cause-specific hazards with Lin-Wei clustering and Aalen-Johansen CIF reveals that Melancholic empathetic agents exhibit elevated hazards '
    'for starvation (CSHR = 1.3058, <i>p</i><sub>Holm</sub> = 0.00035) and acute predation (CSHR = 1.4908, <i>p</i><sub>Holm</sub> = 1.38 &times; 10<sup>-12</sup>), '
    'as well as somatic wear-induced lifespan truncation due to accumulated non-lethal bite penalties (CSHR = 1.5647, <i>p</i><sub>Holm</sub> = 4.49 &times; 10<sup>-62</sup>, rising monotonically to CSHR = 7.32 for &ge; 20 bites). '
    'A dedicated battery of 990 direct mechanistic intervention runs refutes prior conjectures regarding trauma multipliers and anger-dampening, '
    'and achieves experimental pathway isolation for computational oxytocin (&theta;<sub>oxi</sub>): metabolic food transfers (`ALIMENTAR`) account for 74.3% of increased outdoor exposure in tested conditions (DiD &beta; = +4.17 pp, <i>p</i> = 5.29 &times; 10<sup>-9</sup>; seed-cluster bootstrap 95% CI for the share [51.3%, 103.1%], i.e. a wide interval), '
    'while non-trophic affiliative interactions (`ABRAZAR`/`PREGUNTAR`) compete with foraging, elevating starvation mortality (&Delta; = +8.33 pp, <i>p</i><sub>cl</sub> = 0.0319). '
    'In a continuous 7D orthogonal design (<i>G</i> = 75 seeds), &theta;<sub>oxi</sub> is the sole trait surviving Holm-Bonferroni correction over the global family of 21 simultaneous tests (<i>z</i> = +5.85, <i>p</i><sub>Holm, 21</sub> = 1.06 &times; 10<sup>-7</sup>), '
    'while dopamine sensitivity (&theta;<sub>dop</sub>) survives within the 7-trait outdoor exposure domain (<i>z</i> = +2.74, <i>p</i><sub>Holm, 7</sub> = 0.0371). '
    'Crucially, while local neural LLM hooks are implemented as preparatory scaffolding for future developmental ontogenies ("the conscious layer"), '
    '<b>the LLM was inactive during the simulations reported herein</b>. We maintain strict epistemological modesty: '
    'we do not claim full synthetic consciousness, but establish an auditable, homeostatic-causal cybernetic foundation.'
)
story.append(Paragraph(abstract_content, abstract_style))
story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#cbd5e0'), spaceAfter=3))

# =========================================================================
# SECCIÓN 1: INTRODUCCIÓN Y DELIMITACIÓN EPISTEMOLÓGICA
# =========================================================================
story.append(Paragraph('1. Introduction: Symbol Grounding, Epistemic Closure, and Scope of Functional Analogs', h1_style))
story.append(Paragraph(
    'A central debate in cognitive science and artificial intelligence concerns whether disembodied statistical sequence models can exhibit '
    'genuine understanding or intentionality (Searle, 1980; Harnad, 1990). Modern Large Language Models operate through extrinsic statistical '
    'correlations drawn from massive human training corpora, lacking internal homeostatic stakes, real metabolic costs of deliberation, and existential vulnerability. '
    'The guiding philosophy of Project Ascendant is rooted in a pragmatic conviction: <b>the path toward genuine synthetic '
    'consciousness cannot be achieved by expanding ungrounded statistical token predictors alone; it requires embodied, self-directed agency '
    'grounded in homeostatic necessity</b>. We maintain complete intellectual humility regarding this grand challenge. Creating a truly conscious '
    'synthetic entity is a long and demanding scientific journey. <b>The architecture presented here does not claim to possess complete phenomenal sentience '
    'or subjective qualia (Chalmers, 1995), nor do we claim with certainty that we have created synthetic consciousness. The project does not yet possess '
    'sufficient complexity for such claims</b>. Rather, we present a verified autonomous agent driven by virtual visceral desires, capable of self-directed '
    'empirical learning, autobiographical causal replay, and intergenerational cultural accumulation. This work represents the indispensable first milestone: '
    'establishing the cybernetic bedrock upon which future cognitive models—equipped with richer continuous sensory apparatuses and situated in complex, '
    'open-ended environments—can progressively build.',
    body_style
))
story.append(Paragraph(
    'Methodologically, we draw a strict boundary regarding agency and awareness:<br/>'
    '&bull; <b>First-Order Allostatic Behavioral Autonomy:</b> The entity arbitrates its own motor actions by balancing competing internal metabolic imperatives against real environmental affordances.<br/>'
    '&bull; <b>Computational Correlates of Primary and Access Consciousness:</b> Entities exhibit interoceptive valuation, quantifiable attentional trade-offs, autobiographical somatic markers, and dyadic communicative opacity (Damasio, 1994; Dehaene et al., 2017; Panksepp, 1998).<br/>'
    '&bull; <b>Delimitation of Affect and Grief:</b> Upon the death of the progenitor, the system exhibits a <b>simulated grief behavioral response or functional affective state associated with loss</b> '
    '(goal reprioritization, elevation of the dynamic sadness state, transient dampening of exploratory dispersion, and active seeking of alternative attachment bonds). '
    'We have no scientific basis nor empirical evidence to claim phenomenal qualitative suffering or subjective grief.<br/>'
    '&bull; <b>Absence of Second-Order Structural Autopoiesis:</b> The 11-action sensorimotor ontology and homeostatic equation forms represent fixed phylogenetic priors (analogous to evolved subcortical circuits) rather than open-ended self-modifying code.',
    body_style
))

# =========================================================================
# SECCIÓN 2: ARQUITECTURA MATEMÁTICA Y MOTOR MULTI-NIVEL
# =========================================================================
story.append(Paragraph('2. Mathematical Architecture and Multi-Level Cognitive Engine', h1_style))
story.append(Paragraph(
    'Project Ascendant bridges environmental constraints with deliberative arbitration across decoupled, multi-rate operational levels.',
    body_style
))

story.append(Paragraph('2.1. Level 0 &amp; 0.5: Simulated Computational Metabolic Constraints and Caloric Dissipation', h2_style))
story.append(Paragraph(
    'Energy dynamics obey a simulated non-linear metabolic dissipation equation governing the agent\'s in-silico vitality budget:',
    body_style
))
story.append(Paragraph(
    '<i>dE</i><sub><i>i</i></sub>/<i>dt</i> = [&Eacute;<sub>ingest</sub>(<i>t</i>) + &Eacute;<sub>transfer</sub>(<i>t</i>)] - [&beta;<sub>0</sub> + &alpha;<sub><i>v</i></sub> ||<b>v</b><sub>motor</sub>(<i>t</i>)||<sup>1.5</sup> + &gamma;<sub>cold</sub> max(0, <i>T</i><sub>set</sub> - <i>T</i><sub>body</sub>(<i>t</i>))<sup>2</sup> + &kappa;<sub>mental</sub> &middot; <i>C</i><sub>delib</sub>(<i>t</i>)]',
    math_style
))
story.append(Paragraph(
    'Basal maintenance consumes &beta;<sub>0</sub> = 0.05 energy units/cycle, locomotion imposes non-linear drag, and cognitive deliberation incurs a stipulated '
    'computational policy cost (&kappa;<sub>mental</sub> = 0.25 energy units/deliberation cycle). In the simulations reported herein where the local neural LLM was inactive, '
    '<i>C</i><sub>delib</sub>(<i>t</i>) reflects the simulated computational operations of the heuristic prospective planner. We emphasize that this represents '
    '<b>simulated computational metabolic constraints</b> governing agent viability rather than physical hardware thermodynamics (dissipated heat or physical entropy). '
    'Irreversible existential termination (<i>Wipe</i>) occurs if <i>E</i><sub><i>i</i></sub>(<i>t</i>) &le; 0, permanently destroying somatic integrity and episodic memory.',
    body_style
))

story.append(Paragraph('2.2. Level 1: The Limbic Bridge — Separation Between Temperament and Neuroendocrine State', h2_style))
story.append(Paragraph(
    'We formalize a rigorous mathematical distinction between two operational tiers:<br/>'
    '1. <b>Invariable Congenital Temperament:</b> Static vector &theta;<sub>temp</sub> = &lang;&theta;<sub>dop</sub>, &theta;<sub>oxi</sub>, &theta;<sub>ira</sub>, &theta;<sub>tris</sub>, &theta;<sub>res</sub>, &theta;<sub>cur</sub>, cort<sub>base</sub>&rang; &isin; [0.10, 0.90]<sup>7</sup>, representing unalterable constitutional traits.<br/>'
    '2. <b>Dynamic Neuroendocrine State:</b> Continuous fluctuating vector <b>h</b>(<i>t</i>) = &lang;<i>C</i>(<i>t</i>), <i>O</i>(<i>t</i>), <i>D</i>(<i>t</i>), <i>A</i>(<i>t</i>), <i>S</i>(<i>t</i>), <i>R</i>(<i>t</i>), <i>K</i>(<i>t</i>)&rang; &isin; [0.0, 1.0]<sup>7</sup>, integrated via Euler step &Delta;<i>t</i> = 1.0 cycle and clipped to [0, 1]:',
    body_style
))
story.append(Paragraph(
    '<b>Cortisol:</b> <i>dC</i>/<i>dt</i> = -&lambda;<sub><i>c</i></sub>(<i>C</i> - <i>b</i><sub><i>c</i></sub>) + &alpha;<sub><i>c</i></sub> <i>D</i><sub>th</sub> + &beta;<sub><i>c</i></sub> <i>D</i><sub>pred</sub> + &gamma;<sub><i>c</i></sub> <i>D</i><sub>hunger</sub> - &delta;<sub><i>c</i></sub> <i>I</i><sub>shelter</sub><br/>'
    '<b>Oxytocin:</b> <i>dO</i>/<i>dt</i> = -&lambda;<sub><i>o</i></sub>(<i>O</i> - <i>b</i><sub><i>o</i></sub>) + &alpha;<sub><i>o</i></sub> <i>I</i><sub>social_feed</sub> + &beta;<sub><i>o</i></sub> <i>I</i><sub>proximity</sub> - &gamma;<sub><i>o</i></sub> <i>I</i><sub>separation</sub><br/>'
    '<b>Dopamine:</b> <i>dD</i>/<i>dt</i> = -&lambda;<sub><i>d</i></sub>(<i>D</i> - <i>b</i><sub><i>d</i></sub>) + &alpha;<sub><i>d</i></sub> <i>I</i><sub>harvest</sub> + &beta;<sub><i>d</i></sub> <i>I</i><sub>validation</sub> - &gamma;<sub><i>d</i></sub> <i>I</i><sub>loss</sub><br/>'
    '<b>Anger:</b> <i>dA</i>/<i>dt</i> = -&lambda;<sub><i>a</i></sub>(<i>A</i> - <i>b</i><sub><i>a</i></sub>) + &alpha;<sub><i>a</i></sub> <i>D</i><sub>pred</sub> + &beta;<sub><i>a</i></sub> <i>I</i><sub>scarcity</sub> + &gamma;<sub><i>a</i></sub> <i>D</i><sub>hunger</sub> - &delta;<sub><i>a</i></sub> <i>I</i><sub>shelter</sub><br/>'
    '<b>Sadness:</b> <i>dS</i>/<i>dt</i> = -&lambda;<sub><i>s</i></sub>(<i>S</i> - <i>b</i><sub><i>s</i></sub>) + &alpha;<sub><i>s</i></sub> <i>I</i><sub>bereavement</sub> + &beta;<sub><i>s</i></sub> <i>I</i><sub>isolation</sub> - &gamma;<sub><i>s</i></sub> <i>I</i><sub>social_feed</sub><br/>'
    '<b>Resilience:</b> <i>dR</i>/<i>dt</i> = -&lambda;<sub><i>r</i></sub>(<i>R</i> - <i>b</i><sub><i>r</i></sub>) + &alpha;<sub><i>r</i></sub> <i>I</i><sub>survival_streak</sub> - &beta;<sub><i>r</i></sub> <i>I</i><sub>acute_trauma</sub><br/>'
    '<b>Curiosity:</b> <i>dK</i>/<i>dt</i> = -&lambda;<sub><i>k</i></sub>(<i>K</i> - <i>b</i><sub><i>k</i></sub>) + &alpha;<sub><i>k</i></sub> <i>I</i><sub>novelty</sub> - &beta;<sub><i>k</i></sub> <i>D</i><sub>pred</sub> - &gamma;<sub><i>k</i></sub> <i>D</i><sub>hunger</sub>',
    math_style
))
story.append(Paragraph(
    '<i>Epistemological Note on Limbic Variables: The seven state variables are computational constructs inspired by neuroendocrine and affective regulation. '
    'Their numerical values do not represent measured biological hormone concentrations or validated in-vivo physiological dynamics, but rather parameterized '
    'homeostatic control signals within the simulation engine.</i> Visceral hunger drive is non-linearly coupled: '
    '<i>D</i><sub>hunger</sub> = 100 &middot; ((100 - <i>E</i><sub><i>t</i></sub>)/100)<sup>2</sup> &isin; [0, 100].',
    body_style
))

story.append(Paragraph('2.3. Levels 2 &amp; 2.5: Qualitative Interoceptive Representation and Statistical Boundary', h2_style))
story.append(Paragraph(
    'A foundational principle of Ascendant is <b>Strict Epistemic Closure</b>: the deliberative model possesses zero direct access to source code, '
    'memory pointers, raw floating-point floats, or telemetry variables: <i>I</i><sub>Level3</sub>(RAM, Telemetry) = &empty;. '
    'Instead, raw telemetry is mediated by a vertical abstraction layer that acts conceptually as a Markov-blanket-like statistical boundary, '
    'mapping bodily variables into qualitative somatic markers ("<i>stomach gnawing painfully</i>", "<i>limbs shivering in freezing cold</i>", "<i>deep bond of kin proximity</i>"). '
    'While this architecture shares core motivations with active inference (maintaining homeostatic viability against environmental dispersion; Friston, 2010), '
    'we do not claim formal mathematical proofs of variational free energy minimization in the current engine, presenting it instead as a grounded cybernetic system of allostatic control. '
    'Furthermore, language production is strictly decoupled via a <b>centrifugal phonological readout layer</b>: verbalizations serve external observability '
    'and dyadic dialogue, but generated text templates are strictly forbidden from modulating subcortical motor valuation.',
    body_style
))

story.append(Paragraph('2.4. Level 3: Neuro-Inspired Steering and Role of Local LLM as Preparatory Scaffolding', h2_style))
story.append(Paragraph(
    'Ascendant modulates sampling parameters in real time based on the neuroendocrine state: '
    '<i>T</i><sub>sample</sub> = <i>T</i><sub>0</sub> + &kappa;<sub><i>k</i></sub> <i>K</i><sub><i>t</i></sub> - &kappa;<sub><i>c</i></sub> <i>C</i><sub><i>t</i></sub>, '
    'where elevated Curiosity expands stochastic exploration (&kappa;<sub><i>k</i></sub> = 0.35), while acute Cortisol forces focused, conservative, deterministic planning (&kappa;<sub><i>c</i></sub> = 0.40).<br/>'
    '<b>Crucial Methodological Clarification on the LLM Component:</b> The codebase includes integration hooks to local neural language models '
    '(`LIVE_LOCAL_LLM_ENABLED` connecting to local Qwen 2.5 0.5B / Llama-3 endpoints). This component has been implemented specifically as an architectural scaffolding '
    'and preparatory framework for upcoming developmental versions (designed as the future "conscious layer"). '
    '<b>However, for the entire empirical benchmark and causal intervention battery reported in this paper, the local LLM was NOT activated to generate or arbitrate data</b>. '
    'All agent decisions, state transitions, and engram memories were executed deterministically through the high-performance symbolic-heuristic cybernetic engine, '
    'ensuring unconfounded, fully reproducible mathematical dynamics.',
    body_style
))

# =========================================================================
# SECCIÓN 3: COMPROMISOS ATENCIONALES
# =========================================================================
story.append(Paragraph('3. Attention Schema and Somatosensory Cost of Hypothesizing', h1_style))
story.append(Paragraph(
    'Daydreaming and causal prospection are regulated by an Attention Schema (Graziano, 2013). '
    'When idle cycles exceed threshold (&Theta;<sub>idle</sub> &gt; 12 cycles), the agent enters a quiescent resting state, generating prospective hypotheses '
    'and counterfactual engrams in a <b>Latent Deliberation Channel</b> (&xi;<sub>latent</sub> &isin; [0, 1]). '
    'Subcortical motor sovereignty is strictly preserved: acute environmental threats (predator proximity <i>d</i><sub>pred</sub> &lt; 5 m, visceral hunger <i>E</i> &lt; 25) '
    'instantly abort daydreaming via an interrupt vector, restoring reactive motor control without cognitive latency.',
    body_style
))

# =========================================================================
# SECCIÓN 4: MEMORIA AUTOBIOGRÁFICA FINITA Y CLS
# =========================================================================
story.append(Paragraph('4. Finite Chronological Tape and Complementary Learning Systems (CLS)', h1_style))
story.append(Paragraph(
    'Biological agents operate under strict finite memory constraints. Ascendant rejects infinite context windows, implementing a <b>finite chronological tape '
    'of exactly <i>N</i><sub>max</sub> = 100 engrams</b> governed by Complementary Learning Systems (McClelland et al., 1995):<br/>'
    '&bull; <b>Fast Buffer (Recent Episodic Memory):</b> 30 slots capturing recent sensory, affective, and action events with linear recency decay.<br/>'
    '&bull; <b>Slow Consolidated Core (Semantic Heuristics):</b> 70 slots storing crystallized survival rules, parental transmissions, and validated causal schemas.<br/>'
    'When the tape reaches saturation (<i>N</i> = 100), incoming experiences trigger deterministic consolidation: engrams with lowest emotional salience '
    '(&Omega;<sub><i>i</i></sub> = &alpha; |&Delta;<i>C</i><sub><i>i</i></sub>| + &beta; |&Delta;<i>O</i><sub><i>i</i></sub>| + &gamma; <i>R</i><sub>val, <i>i</i></sub>) '
    'are permanently pruned, establishing genuine cognitive forgetting.',
    body_style
))

# =========================================================================
# SECCIÓN 5: ARQUITECTURA INTERGENERACIONAL Y COMPARATIVA
# =========================================================================
story.append(Paragraph('5. Intergenerational Architecture and Comparative Paradigm Taxonomy', h1_style))
story.append(Paragraph(
    'Generational succession operates across parent-child dyads (Ancestral Progenitor <i>P</i><sub>0</sub> &rarr; Alfa &rarr; Beta &rarr; Gama). '
    'Cultural transmission occurs through dyadic dialogue during co-presence in the central sanctuary, transferring validated causal heuristics '
    'into the offspring\'s consolidated memory core. Table 1 situates Project Ascendant relative to dominant paradigms in AI and cognitive modeling.',
    body_style
))

table1_data = [
    [Paragraph('<b>Dimension</b>', table_header),
     Paragraph('<b>Standard LLMs (GPT-4, Gemini)</b>', table_header),
     Paragraph('<b>Embodied RL (MuJoCo, Habitat)</b>', table_header),
     Paragraph('<b>Cognitive Arch. (SOAR, ACT-R)</b>', table_header),
     Paragraph('<b>Active Inference (Friston)</b>', table_header),
     Paragraph('<b>Conscious TM (Blum)</b>', table_header),
     Paragraph('<b>Project Ascendant v4.0 (This Work)</b>', table_header)],
    [Paragraph('<b>Ontology &amp; Substrate</b>', table_text),
     Paragraph('Static neural weights; ungrounded token distribution.', table_text),
     Paragraph('Continuous vector state; scalar reward optimization.', table_text),
     Paragraph('Symbolic production rules; declarative semantic memory.', table_text),
     Paragraph('Generative Markov Blanket; free energy minimization.', table_text),
     Paragraph('Turing machine with short-term memory processor.', table_text),
     Paragraph('<b>Coupled cybernetic hybrid:</b> 7 ODEs + Markov blanket + quiescent prospective planner + 11 motor affordances.', table_text)],
    [Paragraph('<b>Metabolic Vulnerability</b>', table_text),
     Paragraph('Absent; no metabolic penalty or death state.', table_text),
     Paragraph('Absent; typical loss optimization without existential death threshold.', table_text),
     Paragraph('Absent; execution independent of caloric depletion.', table_text),
     Paragraph('Information-theoretic variational bound.', table_text),
     Paragraph('Absent; formal computational abstraction.', table_text),
     Paragraph('<b>Simulated metabolic constraints:</b> Non-linear caloric dissipation, thermal drift, irreversible wipe (<i>E</i> &le; 0).', table_text)],
    [Paragraph('<b>Deliberation Cost</b>', table_text),
     Paragraph('Zero cognitive metabolic penalty.', table_text),
     Paragraph('Fixed step penalty during active environment step.', table_text),
     Paragraph('Zero cognitive metabolic cost.', table_text),
     Paragraph('Free energy trade-off (accuracy vs. complexity).', table_text),
     Paragraph('Computational complexity / step bounds.', table_text),
     Paragraph('<b>Simulated metabolic cost:</b> Deliberation burns explicit caloric reserve (&beta;<sub>delib</sub> = 0.25 c<sup>-1</sup>).', table_text)],
    [Paragraph('<b>Autobiographical Memory</b>', table_text),
     Paragraph('Stateless or static sliding context window.', table_text),
     Paragraph('Finite episodic replay buffer; no semantic reflection.', table_text),
     Paragraph('Declarative memory chunks with power-law decay.', table_text),
     Paragraph('Hierarchical dynamic priors with precision weighting.', table_text),
     Paragraph('Short-term memory tree with conscious broadcast.', table_text),
     Paragraph('<b>Finite chronological tape (<i>N</i>=100):</b> Heuristic dual-zone CLS consolidation &amp; emotional salience pruning.', table_text)],
    [Paragraph('<b>Phenomenal &amp; Affective Scope</b>', table_text),
     Paragraph('Disembodied statistical mimicry without visceral stakes.', table_text),
     Paragraph('Task-specific reward maximization without emotional state.', table_text),
     Paragraph('Functional utility maximization without allostatic embodiment.', table_text),
     Paragraph('Homeostatic interoception as precision steering.', table_text),
     Paragraph('Formal feeling signals (pain, joy) as scalars.', table_text),
     Paragraph('<b>Grounded allostatic drives &amp; functional grief:</b> Coupling of 7 ODEs to motor arbitration (no phenomenal qualia claimed).', table_text)],
    [Paragraph('<b>Decision Hierarchy</b>', table_text),
     Paragraph('Direct prompt-response token sampling.', table_text),
     Paragraph('Direct continuous or discrete policy sampling.', table_text),
     Paragraph('Production matching cycle and conflict resolution.', table_text),
     Paragraph('Policy selection minimizing expected free energy.', table_text),
     Paragraph('Up-tree competition for conscious broadcast.', table_text),
     Paragraph('<b>Two-Tier Control Hierarchy:</b> Quiescent causal planning into latent channel; wakeful subcortical motor sovereignty.', table_text)]
]
t1 = Table(table1_data, colWidths=[66, 76, 76, 78, 80, 80, 84])
t1.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
    ('TOPPADDING', (0, 0), (-1, -1), 1.2),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.2),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.2),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(t1)
story.append(Spacer(1, 2.5))

# =========================================================================
# SECCIÓN 6: RESULTADOS EXPERIMENTALES
# =========================================================================
story.append(PageBreak())
story.append(Paragraph('6. Empirical Results: Multi-Seed Experimental Benchmarks and Intergenerational Factorial Lineage', h1_style))
story.append(Paragraph(
    'We present empirical evaluations across three complementary bodies of data: '
    '(1) Historical Single-Generation Benchmark ($N = 50$ seeds, Engine v1.0), '
    '(2) Factorial Generational Lineage Benchmark ($N = 1,440$ runs across 360 matched seed blocks, Engine v2.4/v4.0), and '
    '(3) The Expanded Causal-Mechanistic Analysis ($N = 38,620$ agents across 9,655 runs in the complete audited relational database).',
    body_style
))

story.append(Paragraph('6.1. Historical Single-Generation Benchmark (N = 50 Seeds): Epistemic Primacy and Spatial Fixation Resolution', h2_style))
story.append(Paragraph(
    'The historical benchmark evaluated the contemporary parent-child dyad under proximal resource distribution (15 m) across 50 Monte Carlo seeds (6,000 cycles). '
    'Prospective daydreaming agents (Ente Alfa) demonstrated dramatic behavioral divergence over reactive agents (Ente Beta), resolving spatial fixation entropy '
    'and establishing the empirical primacy of epistemic somatic retention (<i>R</i><sub>validation</sub> = 205.29 &plusmn; 8.74) over basal caloric intake (<i>R</i><sub>food</sub> = 120.00 &plusmn; 0.00; <i>t</i> = 68.99, <i>p</i> &lt; 10<sup>-45</sup>).<br/>'
    '<i>Methodological Context: This historical single-generation benchmark evaluated Ente Alfa against Ente Beta under Engine v1.0 proximal conditions. '
    'Ente Beta lacked prospective simulation capabilities, resulting in persistent wall collisions and spatial fixation in constrained geometry. '
    'Furthermore, the somatic retention metric (R<sub>val</sub>) was linked to internal hypothesis confirmation routines. All core generational and causal hypotheses '
    'in this paper are evaluated on the new, audited Engine v4.0 (Sections 6.2–6.4), where these historical confounds were eliminated.</i>',
    body_style
))

table2_data = [
    [Paragraph('<b>Cognitive / Behavioral Metric</b>', table_header),
     Paragraph('<b>Ente Alfa (Prospective) [Mean &plusmn; SD]</b>', table_header),
     Paragraph('<b>Ente Beta (Reactive) [Mean &plusmn; SD]</b>', table_header),
     Paragraph('<b>Difference [&Delta;]</b>', table_header),
     Paragraph('<b>Welch <i>t</i>-Test / Significance</b>', table_header)],
    [Paragraph('<b>Survival Rate at 2,000 Cycles</b>', table_text), Paragraph('<b>100.0%</b> (50/50 surviving)', table_text), Paragraph('28.0% (14/50 surviving)', table_text), Paragraph('+72.0%', table_text), Paragraph('&chi;<sup>2</sup> = 56.25, <i>p</i> &lt; 10<sup>-15</sup>', table_text)],
    [Paragraph('<b>Mean Lifespan (Cycles)</b>', table_text), Paragraph('<b>2,000.00 &plusmn; 0.00</b> (uncapped)', table_text), Paragraph('942.30 &plusmn; 418.52', table_text), Paragraph('+1,057.70 cycles', table_text), Paragraph('<i>t</i> = 17.87, <i>p</i> = 3.12 &times; 10<sup>-24</sup>', table_text)],
    [Paragraph('<b>Somatic Retention Validation (<i>R</i><sub>val</sub>)</b>', table_text), Paragraph('<b>205.29 &plusmn; 8.74</b> (Peak Somatic Tag)', table_text), Paragraph('N/A (No hypothesis verification)', table_text), Paragraph('+85.29 over food', table_text), Paragraph('<i>t</i> = 68.99, <i>p</i> &lt; 10<sup>-45</sup> (vs. <i>R</i><sub>food</sub>=120)', table_text)],
    [Paragraph('<b>Peak Cortisol Under Threat</b>', table_text), Paragraph('<b>0.42 &plusmn; 0.08</b> (Allostatic buffer)', table_text), Paragraph('0.89 &plusmn; 0.12 (Severe chronic distress)', table_text), Paragraph('-0.47 units', table_text), Paragraph('<i>t</i> = -22.84, <i>p</i> = 8.44 &times; 10<sup>-29</sup>', table_text)],
    [Paragraph('<b>Daydreaming Rest Cycles</b>', table_text), Paragraph('<b>312.40 &plusmn; 45.20</b> cycles', table_text), Paragraph('0.00 &plusmn; 0.00 cycles (Reactive)', table_text), Paragraph('+312.40 cycles', table_text), Paragraph('<i>t</i> = 48.86, <i>p</i> &lt; 10<sup>-40</sup>', table_text)],
    [Paragraph('<b>Spatial Fixation Entropy</b>', table_text), Paragraph('<b>0.04 &plusmn; 0.01</b> (Goal-directed dispersion)', table_text), Paragraph('0.68 &plusmn; 0.14 (Pathological wall-bumping)', table_text), Paragraph('-0.64 units', table_text), Paragraph('<i>t</i> = -31.75, <i>p</i> &lt; 10<sup>-35</sup>', table_text)]
]
t2 = Table(table2_data, colWidths=[140, 105, 105, 75, 115])
t2.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
    ('TOPPADDING', (0, 0), (-1, -1), 1.2),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.5),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(t2)
story.append(Spacer(1, 2.5))

story.append(Paragraph('6.2. Four-Generation Factorial Benchmark: 2x2 RCBD Seed-Blocked ANOVA (N = 1,440 Runs across 360 Blocks)', h2_style))
story.append(Paragraph(
    '<b>Erratum relative to the earlier draft.</b> A previous draft reported a significant cultural effect on longevity (<i>F</i> = 30.29) and a pantry effect of +781.6 cycles. '
    'Recomputation directly from the frozen SQLite database (script <code>scratch/rcbd_kg.py</code>, deposited with the data) does not reproduce those figures; the values below supersede them. '
    'Cells (mean &plusmn; SD cycles, <i>K</i>=3, <i>M</i>=100): A (T0,P&minus;) 5,998.9 &plusmn; 830.1; B (T0,P+) 6,188.0 &plusmn; 706.6; C (T+,P&minus;) 6,027.8 &plusmn; 812.6; D (T+,P+) 6,201.8 &plusmn; 637.8. '
    'The RCBD model (<i>Y</i><sub><i>s,tp</i></sub> = &mu; + &alpha;<sub><i>T</i></sub><i>T</i> + &beta;<sub><i>P</i></sub><i>P</i> + (&alpha;&beta;)<sub><i>TP</i></sub> + <i>u</i><sub><i>s</i></sub> + &epsilon;) gives '
    'Pantry <i>F</i>(1,1077) = 24.02, <i>p</i> = 1.10 &times; 10<sup>-6</sup>, &eta;<sub><i>p</i></sub><sup>2</sup> = 0.0218; Culture <i>F</i> = 0.33, <i>p</i> = 0.564; Interaction <i>F</i> = 0.042, <i>p</i> = 0.839; '
    'seed blocks <i>F</i>(359,1077) = 1.57, <i>p</i> = 3.4 &times; 10<sup>-8</sup>. Within-seed paired contrasts: pantry without culture +189.10 c (95% CI [73.9, 304.3], <i>t</i> = 3.22); '
    'culture without pantry +28.91 c ([-77.4, 135.2], <i>t</i> = 0.53); interaction &minus;15.10 c ([-147.9, +117.7], <i>t</i> = &minus;0.22), inside the pre-specified &plusmn;250-cycle equivalence margin. '
    'Pooling all six ecological batteries (<i>N</i> = 8,640 runs, 2,160 blocks) yields Pantry <i>F</i>(1,6477) = 519.3 (<i>p</i> = 1.2 &times; 10<sup>-110</sup>, &eta;<sub><i>p</i></sub><sup>2</sup> = 0.0742; +423.5 c, CI [368.1, 478.8]), '
    'Culture <i>F</i> = 0.81 (<i>p</i> = 0.370; +20.4 c, CI [-27.0, 67.8]) and Interaction <i>F</i> = 0.045 (<i>p</i> = 0.833; &minus;7.8 c, CI [-67.5, +52.0]). '
    'Culture therefore does not extend raw cumulative longevity in this engine; it is reported as a null result on this endpoint. Conclusions on additivity are unchanged.',
    body_style
))

table3_data = [
    HD('Source of Variation (RCBD, K=3, M=100)', 'SS', 'df', 'MS', 'F', 'p-Value', 'Partial eta^2', 'Interpretation'),
    R('<b>Culture (T)</b>', '164,224.2', '1', '164,224.2', '0.33', '0.564', '0.0003', 'No detectable effect on raw longevity.'),
    R('<b>Pantry (P)</b>', '11,865,744.9', '1', '11,865,744.9', '<b>24.02</b>', '<b>1.10e-6</b>', '<b>0.0218</b>', 'Buffer against starvation (+189.1 c paired).'),
    R('<b>Interaction (T x P)</b>', '20,520.9', '1', '20,520.9', '0.042', '0.839', '< 0.0001', 'Additive; paired CI [-147.9, +117.7] c within +/-250 c.'),
    R('<b>Seed blocks</b>', '277,670,850.7', '359', '773,456.4', '1.57', '3.4e-8', '-', 'Inter-seed environmental variation.'),
    R('<b>Residual</b>', '531,985,162.0', '1,077', '493,950.9', '-', '-', '-', 'Within-block error.'),
    R('<b>Total</b>', '821,706,502.7', '1,439', '-', '-', '-', '-', '1,440 runs.'),
]
t3 = STY(Table(table3_data, colWidths=[95, 62, 22, 62, 30, 40, 40, 190]))
story.append(t3)
story.append(Spacer(1, 2.5))

story.append(Paragraph('6.3. Mortality Mapping in the Factorial Benchmark and Scope of the Cultural-Ratchet Index', h2_style))
story.append(Paragraph(
    'In the <i>K</i>=3, <i>M</i>=100 battery (1,440 agents per arm, including the progenitor), natural senescence accounts for 78.96% (A), 85.56% (B: pantry), 79.86% (C: culture) and 84.58% (D: both) of deaths, '
    'while starvation deaths fall from 133 (A) and 127 (C) to 59 (B) and 66 (D) &mdash; the pantry, not cultural transmission, is the dominant protective factor. '
    'The regularized cultural index <i>K</i><sub><i>g</i></sub><sup>reg</sup> = (<i>M</i><sub>inn</sub> + <i>M</i><sub>cult</sub> + 1)/(<i>M</i><sub>inn</sub> + 1) is defined for the engram buffer; '
    'however, engram-level records were persisted in the database only for the 990 causal runs (539,201 engrams), so <b>no empirical <i>K</i><sub>g</sub><sup>reg</sup> contrast between T0 and T+ is claimed here</b>. '
    'The values reported in an earlier draft (e.g. 1.206 &plusmn; 0.160) are withdrawn pending re-execution with engram persistence.',
    body_style
))

# =========================================================================
# SECCIÓN 6.4: ANÁLISIS CAUSAL-MECANICISTA, RIESGOS COMPETITIVOS E INTERVENCIONES
# =========================================================================
story.append(PageBreak())
story.append(Paragraph('6.4. Causal Inference, Competing Risks Survival, and Mechanistic Interventions on Congenital Temperament (N = 38,620 Agents)', h1_style))
story.append(Paragraph(
    'To rigorously resolve the relationship between congenital temperament (&theta;<sub>temp</sub> at <i>t</i> = 0) and differential mortality, '
    'we conducted a comprehensive econometric and biostatistical re-analysis of the complete audited database (<b>9,655 runs, 38,620 agents</b>) '
    'comprising 25 BASE runs, 8,640 observational factorial runs and 990 direct mechanistic intervention runs in SQLite (9,655 = 25 + 8,640 + 990; the 990 causal runs decompose as 360 + 150 + 300 + 180 across CAUSAL_0&ndash;3, 4, 5A&ndash;5E and 6A&ndash;6C).',
    body_style
))

story.append(Paragraph('6.4.1. Audit of the New Simulation Engine, Invariants, and Canonical Mortality Resolution', h2_style))
story.append(Paragraph(
    'Two structural invariants were established in the new simulation engine (<code>ejecutar_experimento_generacional.py</code>):<br/>'
    '&bull; <b>Exact -8 Cycle Somatic Bite Wear Invariant:</b> In the predator collision loop, each non-lethal bite deducts 38 energy units and subtracts '
    'exactly <code>transfer_cycles = 8</code> from <code>maxLifespan</code>. For agents dying of natural senescence, age at death equals final lifespan: '
    '<i>n</i><sub>bites, <i>i</i></sub> = (&tau;<sub>0, <i>i</i></sub> - &tau;<sub>final, <i>i</i></sub>) / 8 without rounding error.<br/>'
    '&bull; <b>Strict 4:1 Relational Integrity:</b> The database strictly enforces 9,655 runs &times; 4 agents = 38,620 records with 0 orphan entities.<br/>'
    '&bull; <b>Correction of Pseudoreplication and Cohort Separation:</b> Because the 5 archetypes were seeded identically within blocks across the 24 factorial arms, '
    'treating the 34,560 rows as independent drastically underestimates standard errors. Furthermore, the ancestral progenitor <i>P</i><sub>0</sub> possesses a congenital '
    'telomeric ceiling of &tau;<sub>0</sub> = 800 cycles, while offspring (ALFA, BETA, GAMA) share an identical ceiling of &tau;<sub>0</sub> = 2,000 cycles. '
    'Consequently, all subsequent parametric and semi-parametric inferences are evaluated strictly on the <b>homogeneous cohort of <i>N</i> = 25,920 offspring</b> '
    '(&tau;<sub>0</sub> = 2,000) with variance-covariance matrices clustered across the <b><i>G</i> = 360 independent seeds</b> via Huber-White / Lin-Wei sandwich estimators '
    '(&Delta;DEFF<sub>SE</sub> = 1.11&times;–1.30&times; inflation).<br/>'
    '&bull; <b>Canonical Mortality Audit &amp; Resolution of the 63 Edge-Case Deaths:</b> The canonical database records each agent\'s termination in '
    '<code>final_memories</code> upon cycle exhaustion or lethal strike. Across the <i>N</i> = 25,920 homogeneous offspring, the verified canonical distribution is: '
    '<b>Starvation (<i>n</i> = 3,033, 11.70%)</b>, <b>Acute Predation (<i>n</i> = 4,488, 17.31%)</b>, and <b>Natural Senescence (<i>n</i> = 18,399, 70.98%)</b>. '
    'The audited breakdown across all five archetypes sums exactly to these totals: Coleric (<i>N</i>=4,824: 784 Predation, 528 Starvation, 3,512 Senescence), '
    'Enthusiastic (<i>N</i>=5,448: 957 Predation, 578 Starvation, 3,913 Senescence), Stoic (<i>N</i>=4,800: 729 Predation, 537 Starvation, 3,534 Senescence), '
    'Melancholic (<i>N</i>=5,328: 1,048 Predation, 735 Starvation, 3,545 Senescence), and Optimistic (<i>N</i>=5,520: 970 Predation, 655 Starvation, 3,895 Senescence). '
    'We explicitly document that a 63-death shift observed in a preliminary draft table (which reported 4,551 predation vs 18,336 senescence) arose from an unconstrained script '
    'that categorized agents sustaining non-lethal predator bites on the exact cycle of their vital ceiling boundary (<i>t</i> = &tau;<sub>final</sub>) as predation. '
    'In the canonical database and engine architecture, lethal predation strictly requires acute caloric exhaustion (<i>E</i> &le; 0 via attack), whereas boundary '
    'expiration at <i>t</i> = &tau;<sub>final</sub> is canonically recorded as <code>SENESCENCIA_NATURAL</code>. This harmonization establishes complete mathematical consistency.',
    body_style
))

story.append(Paragraph('6.4.2. Clustered Multinomial Logistic Regression and Average Marginal Effects (AME)', h2_style))
story.append(Paragraph(
    'Evaluating multinomial regression on the 3 competing death categories (Natural Senescence as reference, Starvation, and Acute Predation) '
    'reveals that the congenital temperament block retains an independent, highly significant effect after clustering by seed '
    '(<b>Wald<sub>cl</sub>(8 df) = 67.75, <i>p</i> = 1.38 &times; 10<sup>-11</sup></b>; and Wald<sub>cl</sub>(12 df) = 439.10, <i>p</i> = 1.95 &times; 10<sup>-86</sup> '
    'when distinguishing senescence with vs. without non-lethal bite wear). '
    'However, its explanatory contribution is modest (&Delta;<i>R</i><sup>2</sup><sub>McFadden</sub> = +0.0022 to +0.0092), confirming that <b>temperament is a second-order '
    'behavioral modulator relative to first-order ecological determinants</b> (predator density <i>K</i> = 5 and communal storage, which explain &Delta;<i>R</i><sup>2</sup> = +0.0466).',
    body_style
))

# Tabla 11: Test de Bloques Multinomial
table11_data = [
    HD('Model (N = 25,920, G = 360)', 'Log-lik.', 'R2 McF', 'Delta R2', 'Clustered block statistic', 'df', 'p (cluster)'),
    R('<b>Model 0: Intercepts only (3 cat.)</b>', '-20,683.06', '0.0000', '-', '-', '-', '-'),
    R('<b>Model 1E: Ecology + Generation</b>', '-19,720.16', '0.04656', '+0.04656', 'Wald_cl,eco = 1,208.45', '14', '< 1e-300'),
    R('<b>Model 1A: + Temperament (3 causes)</b>', '-19,674.50', '0.04876', '<b>+0.00221</b>', '<b>Wald_cl,temp = 67.75</b> (LR chi2 = 91.32)', '<b>8</b>', '<b>1.38e-11</b>'),
    R('<b>Model 4C: 4 categories (bite wear), Model 0 / 1E / 4C</b>', '-32,686.98 / -30,191.76 / -29,889.64', '0.08558', '<b>+0.00924</b>', '<b>Wald_cl,temp = 439.10</b> (LR chi2 = 604.24)', '<b>12</b>', '<b>1.95e-86</b>'),
]
t11 = STY(Table(table11_data, colWidths=[150, 95, 40, 45, 120, 25, 55]))
story.append(t11)
story.append(Spacer(1, 2.5))

# Tabla 12: Coeficientes Multinomiales y Efectos Marginales
table12_data = [
    HD('Predictor (vs. Stoic)', 'Outcome', 'beta', 'RRR', '95% CI (cluster)', 'z_cl', 'p_Holm(8)', 'AME (pp +/- SE_cl)'),
    R('<b>Melancholic (oxi=0.86)</b>', 'Starvation', '+0.3387', '<b>1.4031</b>', '[1.2127, 1.6234]', '+4.55', '<b>3.7e-5</b>', '<b>+2.60 +/- 0.79</b>'),
    R('Optimistic (oxi=0.74)', 'Starvation', '+0.1052', '1.1110', '[0.9649, 1.2792]', '+1.46', '0.573', '+0.58 +/- 0.69'),
    R('Enthusiastic (oxi=0.60)', 'Starvation', '-0.0335', '0.9671', '[0.8429, 1.1096]', '-0.48', '1.000', '-0.69 +/- 0.65'),
    R('Choleric (oxi=0.40)', 'Starvation', '-0.0055', '0.9945', '[0.8577, 1.1531]', '-0.07', '1.000', '-0.23 +/- 0.71'),
    R('<b>Melancholic</b>', 'Predation', '+0.3847', '<b>1.4692</b>', '[1.3033, 1.6563]', '+6.29', '<b>2.5e-9</b>', '<b>+4.51 +/- 0.85</b>'),
    R('Optimistic', 'Predation', '+0.2059', '<b>1.2287</b>', '[1.0881, 1.3874]', '+3.32', '0.0054', '+2.51 +/- 0.80'),
    R('Enthusiastic', 'Predation', '+0.1819', '<b>1.1995</b>', '[1.0584, 1.3593]', '+2.85', '0.0219', '+2.49 +/- 0.84'),
    R('Choleric', 'Predation', '+0.0851', '1.0889', '[0.9630, 1.2312]', '+1.36', '0.573', '+1.11 +/- 0.80'),
    R('Ecology K=5 vs K=3', 'Starvation', '+0.8143', '<b>2.2575</b>', '[2.0535, 2.4818]', '+16.85', '< 1e-60', '<b>+6.12 +/- 0.46</b>'),
    R('Ecology K=5 vs K=3', 'Predation', '+0.8969', '<b>2.4521</b>', '[2.2611, 2.6592]', '+21.68', '< 1e-100', '<b>+10.65 +/- 0.54</b>'),
    R('Communal Pantry vs none', 'Starvation', '-1.0992', '<b>0.3331</b>', '[0.2988, 0.3715]', '-19.78', '< 1e-85', '<b>-9.34 +/- 0.50</b>'),
    R('Communal Pantry vs none', 'Predation', '-0.6113', '<b>0.5426</b>', '[0.5004, 0.5884]', '-14.80', '< 1e-48', '<b>-6.16 +/- 0.55</b>'),
]
t12 = STY(Table(table12_data, colWidths=[95, 50, 40, 40, 85, 35, 50, 90]))
story.append(t12)
story.append(Spacer(1, 2.5))

story.append(Paragraph('6.4.3. Competing Risks Survival: Cox Cause-Specific Hazards (CSHR) and Somatic Wear Truncation', h2_style))
story.append(Paragraph(
    'Because starvation, acute predation, and senescent ceiling exhaustion mutually censor one another at exact event times <i>T</i><sub><i>i</i></sub> &isin; [1, 2,000], '
    'we fit Cox-Breslow cause-specific proportional hazards models with Lin-Wei sandwich variance across the 43.60 million agent-cycles of tracking '
    '(Table 13). Melancholic agents exhibit higher instantaneous hazards for both acute causes (Starvation CSHR = 1.3058, <i>p</i> = 0.00035; '
    'Predation CSHR = 1.4908, <i>p</i> = 1.38 &times; 10<sup>-12</sup>). '
    'Furthermore, non-lethal predator bites deduct exactly -8 cycles from the vital ceiling, resulting in <b>somatic wear-induced lifespan truncation / '
    'rule-governed ceiling depletion</b> (CSHR<sub>sen</sub> = 1.5647, <i>z</i> = +16.71, <i>p</i><sub>Holm</sub> = 4.49 &times; 10<sup>-62</sup>). '
    'We explicitly clarify that this elevated hazard ratio captures the cumulative operation of the engine\'s wear invariant (&Delta;&tau;<sub>max</sub> = -8 c/bite) '
    'rather than an autonomous discovery of biological senescence. Evaluating a sensitivity grid of cumulative somatic wear (&ge; 1, &ge; 5, &ge; 10, &ge; 15, &ge; 20 bites) '
    'shows that the excess hazard grows monotonically from 1.57&times; to 1.64&times;, 2.24&times;, 3.56&times;, and 7.32&times; (Table 14). '
    'Diagnostics: ties are moderate (starvation: 3,033 events at 1,390 distinct cycles, mean 2.18, max 14; predation: 4,488 events at 1,563 cycles, mean 2.87, max 52; Breslow handling applied). '
    'An approximate time-trend diagnostic for proportional hazards (correlation of the Melancholic indicator with log <i>t</i> among Melancholic+Stoic failures) is non-significant for starvation (<i>r</i> = 0.042, <i>p</i> = 0.136) and predation (<i>r</i> = 0.039, <i>p</i> = 0.105); '
    'piecewise hazard ratios (cycles 1&ndash;1000 vs 1001&ndash;2000) are 1.22 vs 1.36 (starvation) and 1.27 vs 1.43 (predation), indicating mild, non-significant strengthening over age. '
    'Because senescence is truncated at the ceiling (18,379 of 18,399 senescent deaths occur before <i>t</i> = 2,000; 20 exactly at 2,000), the all-cause premature-mortality model (starvation + predation as events, 7,521 events) is also reported: '
    'Wald<sub>cl</sub>(4) = 78.76 (<i>p</i> = 3.2 &times; 10<sup>-16</sup>); Melancholic CSHR = 1.4082 [1.2992, 1.5265] (<i>p</i><sub>Holm</sub> = 3.4 &times; 10<sup>-16</sup>), Optimistic 1.1864 [1.0895, 1.2920], Enthusiastic 1.1076 [1.0195, 1.2034] (<i>p</i><sub>Holm</sub> = 0.031), Choleric 1.0601 [0.9717, 1.1564] (<i>p</i><sub>Holm</sub> = 0.189).',
    body_style
))

# Tabla 13: Modelos de Cox por Causa Específica
story.append(FIG('fig1_cif_aalen_johansen.png', '<b>Figure 1.</b> Aalen-Johansen cumulative incidence of starvation (A) and acute predation (B) by congenital archetype (N = 25,920 offspring, G = 360 seeds). Legend gives CIF(2000) for starvation | predation.'))
table13_data = [
    HD('Cause (N = 25,920, G = 360)', 'Contrast vs. Stoic', 'Events', 'beta', 'CSHR', '95% CI (Lin-Wei)', 'z_cl', 'p_Holm', 'CIF(2000)'),
    R('<b>Starvation</b> (Wald_cl(4) = 28.43, p = 1.0e-5)', '<b>Melancholic</b> (oxi=0.86)', '735 / 5,328', '+0.2668', '<b>1.3058</b>', '[1.1428, 1.4921]', '+3.92', '<b>0.00035</b>', '<b>13.80%</b>'),
    R('Starvation (3,033 total)', 'Optimistic', '655 / 5,520', '+0.0708', '1.0733', '[0.9440, 1.2204]', '+1.08', '0.840', '11.87%'),
    R('Starvation', 'Enthusiastic', '578 / 5,448', '-0.0650', '0.9371', '[0.8252, 1.0641]', '-1.00', '0.840', '10.61%'),
    R('Starvation', 'Choleric', '528 / 4,824', '-0.0197', '0.9805', '[0.8551, 1.1243]', '-0.28', '0.840', '10.95%'),
    R('Starvation (reference)', 'Stoic (oxi=0.22)', '537 / 4,800', '0', '1.0000', 'Baseline', '-', '-', '11.19%'),
    R('<b>Acute Predation</b> (Wald_cl(4) = 58.37, p = 6.4e-12)', '<b>Melancholic</b>', '1,048 / 5,328', '+0.3993', '<b>1.4908</b>', '[1.3388, 1.6602]', '+7.28', '<b>1.38e-12</b>', '<b>19.67%</b>'),
    R('Acute Predation (4,488 total)', 'Optimistic', '970 / 5,520', '+0.2450', '<b>1.2777</b>', '[1.1437, 1.4273]', '+4.34', '<b>4.3e-5</b>', '17.57%'),
    R('Acute Predation', 'Enthusiastic', '957 / 5,448', '+0.2196', '<b>1.2456</b>', '[1.1113, 1.3961]', '+3.77', '<b>0.00032</b>', '17.57%'),
    R('Acute Predation', 'Choleric', '784 / 4,824', '+0.1146', '<b>1.1214</b>', '[1.0007, 1.2568]', '+1.97', '<b>0.0487</b>', '16.25%'),
    R('Acute Predation (reference)', 'Stoic', '729 / 4,800', '0', '1.0000', 'Baseline', '-', '-', '15.19%'),
    R('<b>Wear-truncated senescence</b> (Wald_cl(4) = 377.87)', '<b>Melancholic</b> vs. Stoic', '3,545 / 5,328 vs 3,534 / 4,800', '+0.4477', '<b>1.5647</b>', '[1.4846, 1.6490]', '+16.71', '<b>4.5e-62</b>', '<b>66.54%</b> vs 73.63%'),
]
t13 = STY(Table(table13_data, colWidths=[85, 75, 62, 38, 38, 70, 32, 42, 55]))
story.append(t13)
story.append(Spacer(1, 2.5))

# Tabla 14: Rejilla de Sensibilidad de Desgaste por Mordiscos
table14_data = [
    HD('Somatic wear threshold', 'Ceiling loss', 'Total events', 'Melancholic incid.', 'Stoic incid.', 'CSHR Mel vs Sto', '95% CI', 'z_cl', 'p (cluster)'),
    R('<b>>= 1 non-lethal bite</b>', '<= -8 c', '18,379 (70.91%)', '66.42% (3,539/5,328)', '73.50% (3,528/4,800)', '<b>1.5658</b>', '[1.4856, 1.6502]', '+16.72', '8.9e-63'),
    R('<b>>= 5 bites</b>', '<= -40 c', '16,568 (63.92%)', '61.28% (3,265/5,328)', '63.90% (3,067/4,800)', '<b>1.6350</b>', '[1.5473, 1.7277]', '+17.47', '2.3e-68'),
    R('<b>>= 10 bites</b>', '<= -80 c', '8,396 (32.39%)', '<b>36.11%</b> (1,924/5,328)', '<b>23.58%</b> (1,132/4,800)', '<b>2.2390</b>', '[2.0554, 2.4389]', '+18.47', '3.6e-76'),
    R('<b>>= 15 bites</b>', '<= -120 c', '1,960 (7.56%)', '<b>9.83%</b> (524/5,328)', '<b>3.44%</b> (165/4,800)', '<b>3.5647</b>', '[2.9235, 4.3464]', '+12.56', '3.3e-36'),
    R('<b>>= 20 bites</b>', '<= -160 c', '231 (0.89%)', '<b>1.58%</b> (84/5,328)', '<b>0.25%</b> (12/4,800)', '<b>7.3215</b>', '[4.1863, 12.8048]', '+6.98', '2.9e-12'),
]
t14 = STY(Table(table14_data, colWidths=[75, 45, 60, 80, 80, 50, 70, 35, 40]))
story.append(KeepTogether(t14))
story.append(Spacer(1, 2.5))
story.append(FIG('fig2_cox_and_bite_wear.png', '<b>Figure 2.</b> (A) Cause-specific hazard ratios with Lin-Wei seed-clustered 95% CI for all four archetypes versus Stoic; (B) bite-wear sensitivity grid for Melancholic vs Stoic.'))

story.append(Paragraph('6.4.4. Expanded Direct Mechanistic Interventions and Behavioral Pathway Isolation (990 Runs in SQLite)', h2_style))
story.append(Paragraph(
    'To transition from observational association to verified causation within the simulator, we executed a dedicated battery of 990 simulation runs '
    'performing direct code-level counterfactual surgery (<i>do</i>-calculus). Findings refute prior conjectures and identify the exact behavioral pathways:<br/>'
    '&bull; <b>Trauma sensitivity and anger-dampening (corrected equations):</b> In engine v4.0 trauma processing is governed by two explicit terms. '
    '(i) The inherited-trauma multiplier <i>M</i><sub>inh</sub>(<b>h</b>) = (0.55 <i>h</i><sub>tris</sub> + 0.45 <i>h</i><sub>oxi</sub>) / (0.65 <i>h</i><sub>res</sub> + 0.35); evaluated at the congenital set-points it equals 1.413 (Melancholic), 0.501 (Optimistic), 0.494 (Enthusiastic), 0.482 (Choleric) and 0.270 (Stoic), so Melancholic and Choleric agents do <b>not</b> share an identical multiplier (an earlier draft used a superseded v3 formula, (0.7+tris)(1.3&minus;res), giving 1.4112). '
    '(ii) Under acute hunger (<i>E</i> &lt; 35) trauma attenuation is &alpha;<sub>trauma</sub> = clip(((<i>E</i>&minus;8)/27) / max(0.15, <i>D</i><sub>desp</sub>), 0.12, 1) with <i>D</i><sub>desp</sub> = 0.60 <i>h</i><sub>ira</sub> + 0.40 <i>h</i><sub>res</sub> (0.232, 0.412, 0.424, 0.708, 0.448 for Mel., Opt., Ent., Chol., Stoic). '
    'Ablating the anger term in (ii) (`CAUSAL_3_NO_IRA`, 90 paired runs, 270 offspring) is inert on outside exposure (&Delta; = +0.42 pp, <i>p</i><sub>cl</sub> = 0.708) and predation mortality (&Delta; = -0.37 pp, <i>p</i><sub>cl</sub> = 0.920).<br/>'
    '&bull; <b>Surgical Swap of &theta;<sub>oxi</sub> (`CAUSAL_1_SWAP_OXI`, 90 runs, 270 offspring):</b> Injecting <i>do</i>(&theta;<sub>oxi</sub> = 0.86) into the Stoic archetype '
    'triples its starvation mortality from 7.14% (3/42) to 23.81% (10/42, &Delta; = +16.67 pp, <i>p</i><sub>cl</sub> = 0.0414), while reducing senescent survival by -22.41 pp (<i>p</i><sub>Fisher</sub> = 0.0162).<br/>'
    '&bull; <b>Factorial Experimental Pathway Isolation (`CAUSAL_5A–5E`, 300 runs, 900 offspring across 30 seeds):</b> '
    'Difference-in-Differences interaction demonstrates that the metabolic transfer action `ALIMENTAR` (Eq. 3.2: +1.8 &middot; oxi) '
    'accounts for <b>74.3% of the observed increase in outdoor risk exposure across the tested conditions</b> (&beta;<sub>DiD</sub> = +4.17 pp, <i>p</i> = 5.29 &times; 10<sup>-9</sup>), '
    'doubling predation mortality when acting alone (`5E` vs. `5A`: 10.00% &rarr; 18.89%, &Delta; = +8.89 pp, <i>p</i><sub>cl</sub> = 0.0271). '
    'Conversely, unblocking non-trophic affiliative cohesion (`ABRAZAR`/`PREGUNTAR`, `5B` vs. `5E`) adds +25.5 social actions/1k, adds +2.45 pp exposure, '
    'and significantly elevates starvation mortality from 11.67% to 20.00% (&Delta; = +8.33 pp, <i>p</i><sub>cl</sub> = 0.0319). '
    'We emphasize that this 74.3% partition represents an empirical decomposition dependent on the tested intervention arms and engine rules, '
    'rather than a universal mediation parameter. A seed-cluster bootstrap (10,000 resamples over G = 30 seeds) gives total exposure effect 5B vs 5A = +5.61 pp (95% CI [4.27, 7.01]), DiD interaction +4.17 pp ([2.82, 5.57]) and a pathway share of 74.3% with 95% CI [51.3%, 103.1%] (SE 13.0%); the interval includes 100%, so the point share should be read as approximate (a pure-feeding contrast 5E vs 5A gives 56.2%, CI [34.4%, 83.1%]). <b>Starvation mortality in high-oxytocin agents emerges from the synergistic drain of metabolic donation combined with affiliative delay</b>.',
    body_style
))

story.append(Paragraph(
    '<b>Structural causal model.</b> The interventional design is formalized as <i>M</i> = &lang;<i>U</i>, <i>V</i>, <i>F</i>&rang; (Pearl, 2009). Exogenous variables <i>U</i> are the seed-determined Mulberry32 pseudo-random stream (environment layout, congenital jitter &theta; = base &times; (0.92 + 0.16<i>u</i>)). '
    'Endogenous variables <i>V</i> comprise congenital vector &theta;<sub>temp</sub>, neuroendocrine state <b>h</b>(<i>t</i>), actions (ALIMENTAR, ABRAZAR, PREGUNTAR, forage), outside-exposure ratio, bite count and cause of death. '
    'The structural functions <i>F</i> are the deterministic engine update rules (Section 2 and 7). Interventions are implemented in code as <i>do</i>(&theta;<sub>oxi</sub> = <i>c</i>), <i>do</i>(<i>g</i><sub>feed</sub> = 0 or dose), <i>do</i>(<i>g</i><sub>ira</sub> = 0) and <i>do</i>(&theta;<sub>nonfeed,oxi</sub> = 0.22). '
    'Estimands are average treatment effects in percentage points on offspring outcomes within seed-matched arms, with seed-clustered standard errors (G = 30&ndash;75) and Fisher exact tests for 2&times;2 counts; the 74.3% share is the DiD interaction divided by the total effect.',
    body_style
))

# Tabla 14B: Trazabilidad de Denominadores de las Intervenciones
table14b_data = [
    [Paragraph('<b>Experiment Tag &amp; Arm</b>', table_header),
     Paragraph('<b>Mechanistic Intervention Description</b>', table_header),
     Paragraph('<b>Runs</b>', table_header),
     Paragraph('<b>Total Ag.</b>', table_header),
     Paragraph('<b><i>P</i><sub>0</sub> Excl.</b>', table_header),
     Paragraph('<b>Eligible Offs.</b>', table_header),
     Paragraph('<b>Analyzed Sub-Cohort</b>', table_header),
     Paragraph('<b>Seeds (<i>G</i>)</b>', table_header),
     Paragraph('<b>Design Structure</b>', table_header)],
    [Paragraph('<b>CAUSAL_0_CONTROL</b>', table_text), Paragraph('Natural baseline dynamics (no intervention)', table_text), Paragraph('90', table_text), Paragraph('360', table_text), Paragraph('90', table_text), Paragraph('270', table_text), Paragraph('42 Stoic, 64 Melanc. (270 total)', table_text), Paragraph('45', table_text), Paragraph('Seed-Paired Baseline', table_text)],
    [Paragraph('<b>CAUSAL_1_SWAP_OXI</b>', table_text), Paragraph('Surgical swap <i>do</i>(&theta;<sub>oxi</sub>=0.86) into Stoics', table_text), Paragraph('90', table_text), Paragraph('360', table_text), Paragraph('90', table_text), Paragraph('270', table_text), Paragraph('42 Stoic, 64 Melanc. (270 total)', table_text), Paragraph('45', table_text), Paragraph('Seed-Paired with Ctrl', table_text)],
    [Paragraph('<b>CAUSAL_5A–5E</b>', table_text), Paragraph('2&times;2 Factorial pathway isolation (5 arms &times; 60)', table_text), Paragraph('300', table_text), Paragraph('1,200', table_text), Paragraph('300', table_text), Paragraph('900', table_text), Paragraph('180 offspring / arm (900 total)', table_text), Paragraph('30', table_text), Paragraph('Matched across 5 arms', table_text)],
    [Paragraph('<b>CAUSAL_3_ABL_IRA</b>', table_text), Paragraph('Ablation of anger denominator (Eq. 2.11)', table_text), Paragraph('90', table_text), Paragraph('360', table_text), Paragraph('90', table_text), Paragraph('270', table_text), Paragraph('38 Choleric (270 total)', table_text), Paragraph('45', table_text), Paragraph('Seed-Paired with Ctrl', table_text)],
    [Paragraph('<b>CAUSAL_2_ABL_FEED</b>', table_text), Paragraph('Ablation of feeding transfer (`ALIMENTAR`)', table_text), Paragraph('90', table_text), Paragraph('360', table_text), Paragraph('90', table_text), Paragraph('270', table_text), Paragraph('64 Melanc. (270 total)', table_text), Paragraph('45', table_text), Paragraph('Seed-Paired with Ctrl', table_text)],
    [Paragraph('<b>CAUSAL_4_ORTHO_7D</b>', table_text), Paragraph('Continuous 7D orthogonal trait sampling', table_text), Paragraph('150', table_text), Paragraph('600', table_text), Paragraph('150', table_text), Paragraph('450', table_text), Paragraph('450 homogeneous offspring', table_text), Paragraph('75', table_text), Paragraph('Independent Orthogonal', table_text)],
    [Paragraph('<b>CAUSAL_6A–6C</b>', table_text), Paragraph('Dose-response donation grid (0.5&times;, 1.5&times;, 2.0&times;)', table_text), Paragraph('180', table_text), Paragraph('720', table_text), Paragraph('180', table_text), Paragraph('540', table_text), Paragraph('180 offspring / arm (540 total)', table_text), Paragraph('30', table_text), Paragraph('Matched across 3 doses', table_text)]
]
t14b = Table(table14b_data, colWidths=[80, 125, 24, 34, 34, 38, 95, 36, 74])
t14b.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.0),
    ('TOPPADDING', (0, 0), (-1, -1), 1.0),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.0),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(KeepTogether(t14b))
story.append(Spacer(1, 2.5))

# Tabla 15: Experimentos Causales
table15_data = [
    [Paragraph('<b>Experiment &amp; Intervention</b>', table_header),
     Paragraph('<b>Condition / Arm</b>', table_header),
     Paragraph('<b><i>n</i></b>', table_header),
     Paragraph('<b>Donations / 1k</b>', table_header),
     Paragraph('<b>Outside Exp.</b>', table_header),
     Paragraph('<b>Mean Age</b>', table_header),
     Paragraph('<b>Starvation <i>k/n</i> (%)</b>', table_header),
     Paragraph('<b>Predation <i>k/n</i> (%)</b>', table_header),
     Paragraph('<b>Causal Contrast &amp; Significance</b>', table_header)],
    [Paragraph('<b>Exp 1: Swap &theta;<sub>oxi</sub> (Stoic)</b>', table_text), Paragraph('Control (&theta;<sub>oxi</sub>=0.22)', table_text), Paragraph('42', table_text), Paragraph('10.20', table_text), Paragraph('22.79%', table_text), Paragraph('1,750 c', table_text), Paragraph('3/42 (7.14%)', table_text), Paragraph('8/42 (19.05%)', table_text), Paragraph('Baseline Stoic', table_text)],
    [Paragraph('<b>Exp 1: Swap &theta;<sub>oxi</sub> (Stoic)</b>', table_text), Paragraph('Swap <i>do</i>(&theta;<sub>oxi</sub>=0.86)', table_text), Paragraph('42', table_text), Paragraph('<b>11.98</b>', table_text), Paragraph('<b>26.72%</b>', table_text), Paragraph('<b>1,505 c</b>', table_text), Paragraph('<b>10/42 (23.81%)</b>', table_text), Paragraph('8/42 (19.05%)', table_text), Paragraph('<b>&Delta; = +16.67 pp</b> (<i>p</i><sub>cl</sub> = 0.0414)', table_text)],
    [Paragraph('<b>Exp 4: Factorial Pathway Isolation</b>', table_text), Paragraph('5A: Low Oxi, Feed Active', table_text), Paragraph('180', table_text), Paragraph('5.90', table_text), Paragraph('20.75%', table_text), Paragraph('1,728 c', table_text), Paragraph('30/180 (16.67%)', table_text), Paragraph('18/180 (10.00%)', table_text), Paragraph('Low oxytocin baseline', table_text)],
    [Paragraph('<b>Exp 4: Factorial Pathway Isolation</b>', table_text), Paragraph('5E: High Oxi in Feed Only', table_text), Paragraph('180', table_text), Paragraph('<b>11.78</b>', table_text), Paragraph('<b>23.91%</b>', table_text), Paragraph('1,662 c', table_text), Paragraph('21/180 (11.67%)', table_text), Paragraph('<b>34/180 (18.89%)</b>', table_text), Paragraph('<b>&Delta;<sub>depr</sub> = +8.89 pp</b> (<i>p</i><sub>cl</sub> = 0.0271)', table_text)],
    [Paragraph('<b>Exp 4: Factorial Pathway Isolation</b>', table_text), Paragraph('5B: High Oxi Full Synergy', table_text), Paragraph('180', table_text), Paragraph('<b>11.55</b>', table_text), Paragraph('<b>26.36%</b>', table_text), Paragraph('1,602 c', table_text), Paragraph('<b>36/180 (20.00%)</b>', table_text), Paragraph('24/180 (13.33%)', table_text), Paragraph('<b>&Delta;<sub>inan</sub> = +8.33 pp vs 5E</b> (<i>p</i><sub>cl</sub> = 0.0319)', table_text)],
    [Paragraph('<b>Exp 3: Anger Ablation (Ec. 2.11)</b>', table_text), Paragraph('CAUSAL_3_NO_IRA', table_text), Paragraph('270', table_text), Paragraph('—', table_text), Paragraph('25.39%', table_text), Paragraph('1,604 c', table_text), Paragraph('44/270 (16.30%)', table_text), Paragraph('54/270 (20.00%)', table_text), Paragraph('Inert: &Delta; = -0.37 pp (<i>p</i><sub>cl</sub> = 0.920)', table_text)],
    [Paragraph('<b>Exp 2: Feed Ablation (Melanc.)</b>', table_text), Paragraph('CAUSAL_2_NO_FEED', table_text), Paragraph('64', table_text), Paragraph('0.00', table_text), Paragraph('<b>20.06%</b> (-6.3 pp)', table_text), Paragraph('<b>1,587 c</b> (+69 c)', table_text), Paragraph('8/64 (12.50%)', table_text), Paragraph('14/64 (21.88%)', table_text), Paragraph('Starvation drops -6.25 pp', table_text)],
    [Paragraph('<b>Exp 5: Dose-Response Grid</b>', table_text), Paragraph('<i>g</i> = 0.0 &rarr; <i>g</i> = 2.0', table_text), Paragraph('540', table_text), Paragraph('0.0 &rarr; 10.7/1k', table_text), Paragraph('19.1% &rarr; 25.1%', table_text), Paragraph('-135.7 c loss', table_text), Paragraph('13.9% &rarr; 15.6%', table_text), Paragraph('15.0% &rarr; 20.0%', table_text), Paragraph('Kinetic saturation at <i>c</i> &ge; 1.8', table_text)]
]
t15 = Table(table15_data, colWidths=[80, 75, 25, 52, 50, 48, 65, 65, 80])
t15.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.0),
    ('TOPPADDING', (0, 0), (-1, -1), 1.0),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.0),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(KeepTogether(t15))
story.append(Spacer(1, 2.5))

story.append(Paragraph('6.4.5. Continuous 7D Orthogonal Trait Sampling: Defining Holm-Bonferroni Correction Families (G = 75 Seeds)', h2_style))
story.append(Paragraph(
    'Sampling all 7 congenital traits independently (&Uscr;(0.15, 0.95), |&rho;<sub>max</sub>| &lt; 0.05 at <i>t</i> = 0) enables unconfounded parameter estimation. '
    'We explicitly distinguish two pre-specified hypothesis testing families:<br/>'
    '&bull; <b>Primary Global Family (<i>m</i> = 21 tests):</b> Across all 7 traits &times; 3 core endpoints (donations, outside exposure, starvation odds), '
    '<b>congenital oxytocin (&theta;<sub>oxi</sub>) is the sole trait that survives Holm-Bonferroni correction</b> for both donations '
    '(<i>z</i> = +5.85, <b><i>p</i><sub>Holm, 21</sub> = 1.06 &times; 10<sup>-7</sup></b>) and exterior exposure '
    '(<i>z</i> = +5.12, <b><i>p</i><sub>Holm, 21</sub> = 6.09 &times; 10<sup>-6</sup></b>), with starvation odds increasing by +3.91 pp/SD (OR = 1.354, <i>p</i><sub>raw</sub> = 0.034).<br/>'
    '&bull; <b>Secondary Behavioral Domain Family (<i>m</i> = 7 tests):</b> Within the specific domain of outdoor exposure ratio, '
    '<b>congenital dopamine (&theta;<sub>dop</sub>) also reaches statistical significance</b> (+0.967 pp/SD, <b><i>p</i><sub>Holm, 7</sub> = 0.0371</b>), '
    'while exerting a protective effect against starvation (-3.66 pp/SD, OR = 0.755, <i>p</i><sub>raw</sub> = 0.0394) by directing outdoor activity toward food harvesting.<br/>'
    '<b>Interaction audit.</b> Synergy terms oxytocin &times; low resilience and oxytocin &times; sadness (joint 3-df cluster Wald) are not significant for exposure (<i>p</i> = 0.554; oxi&times;(&minus;res) &beta; = +0.52 pp, <i>p</i> = 0.172), starvation (<i>p</i> = 0.183) or predation (<i>p</i> = 0.344); with N = 450 the design has limited power for interactions.<br/>'
    'We note that while traits are strictly orthogonalized at <i>t</i> = 0, this does not imply absolute causal independence throughout downstream non-linear behavioral feedback loops.',
    body_style
))

# Tabla 16: Regresión Ortogonal 7D con Holm-Bonferroni
table16_data = [
    [Paragraph('<b>Continuous Trait (&Uscr;(0.15,0.95))</b>', table_header),
     Paragraph('<b>Donations/1k (&Delta;/SD)</b>', table_header),
     Paragraph('<b><i>z</i><sub>cl</sub> (<i>p</i><sub>Holm, 21</sub>)</b>', table_header),
     Paragraph('<b>Outside Exp. (&Delta;/SD)</b>', table_header),
     Paragraph('<b><i>z</i><sub>cl</sub> (<i>p</i><sub>Holm, 21</sub>)</b>', table_header),
     Paragraph('<b>Starvation OR (95% CI)</b>', table_header),
     Paragraph('<b><i>z</i><sub>cl</sub> (<i>p</i><sub>raw</sub> / <i>p</i><sub>H7</sub>)</b>', table_header),
     Paragraph('<b>Predation OR (<i>p</i><sub>raw</sub>)</b>', table_header)],
    [Paragraph('<b>1. Oxytocin (&theta;<sub>oxi</sub>)</b>', table_text), Paragraph('<b>+1.430 &plusmn; 0.245</b>', table_text), Paragraph('<b>+5.85 (1.1&times;10<sup>-7</sup>)</b>', table_text), Paragraph('<b>+1.973 &plusmn; 0.385 pp</b>', table_text), Paragraph('<b>+5.12 (6.1&times;10<sup>-6</sup>)</b>', table_text), Paragraph('<b>1.354 [1.023, 1.792]</b>', table_text), Paragraph('<b>+2.12 (0.034 / 0.238)</b>', table_text), Paragraph('1.018 (<i>p</i>=0.882)', table_text)],
    [Paragraph('<b>2. Dopamine (&theta;<sub>dop</sub>)</b>', table_text), Paragraph('+0.332 &plusmn; 0.266', table_text), Paragraph('+1.25 (1.00)', table_text), Paragraph('<b>+0.967 &plusmn; 0.353 pp</b>', table_text), Paragraph('<b>+2.74 (0.037)</b>', table_text), Paragraph('<b>0.755 [0.579, 0.986]</b>', table_text), Paragraph('<b>-2.06 (0.039 / 0.238)</b>', table_text), Paragraph('1.230 (<i>p</i>=0.095)', table_text)],
    [Paragraph('<b>3. Anger (&theta;<sub>ira</sub>)</b>', table_text), Paragraph('-0.385 &plusmn; 0.280', table_text), Paragraph('-1.37 (1.00)', table_text), Paragraph('+0.038 &plusmn; 0.381 pp', table_text), Paragraph('+0.10 (1.00)', table_text), Paragraph('0.862 [0.657, 1.131]', table_text), Paragraph('-1.07 (0.284 / 1.00)', table_text), Paragraph('1.078 (<i>p</i>=0.514)', table_text)],
    [Paragraph('<b>4. Sadness (&theta;<sub>tris</sub>)</b>', table_text), Paragraph('-0.204 &plusmn; 0.246', table_text), Paragraph('-0.83 (1.00)', table_text), Paragraph('+0.063 &plusmn; 0.362 pp', table_text), Paragraph('+0.17 (1.00)', table_text), Paragraph('1.059 [0.807, 1.390]', table_text), Paragraph('+0.41 (0.681 / 1.00)', table_text), Paragraph('1.021 (<i>p</i>=0.877)', table_text)],
    [Paragraph('<b>5. Resilience (&theta;<sub>res</sub>)</b>', table_text), Paragraph('-0.150 &plusmn; 0.255', table_text), Paragraph('-0.59 (1.00)', table_text), Paragraph('-0.642 &plusmn; 0.413 pp', table_text), Paragraph('-1.55 (1.00)', table_text), Paragraph('0.935 [0.706, 1.238]', table_text), Paragraph('-0.47 (0.639 / 1.00)', table_text), Paragraph('1.087 (<i>p</i>=0.486)', table_text)],
    [Paragraph('<b>6. Curiosity (&theta;<sub>cur</sub>)</b>', table_text), Paragraph('+0.433 &plusmn; 0.276', table_text), Paragraph('+1.57 (1.00)', table_text), Paragraph('+0.083 &plusmn; 0.352 pp', table_text), Paragraph('+0.23 (1.00)', table_text), Paragraph('1.039 [0.763, 1.417]', table_text), Paragraph('+0.25 (0.806 / 1.00)', table_text), Paragraph('1.076 (<i>p</i>=0.525)', table_text)],
    [Paragraph('<b>7. Base Cortisol (cort<sub>base</sub>)</b>', table_text), Paragraph('+0.077 &plusmn; 0.300', table_text), Paragraph('+0.26 (1.00)', table_text), Paragraph('-0.240 &plusmn; 0.398 pp', table_text), Paragraph('-0.60 (1.00)', table_text), Paragraph('1.022 [0.818, 1.276]', table_text), Paragraph('+0.19 (0.849 / 1.00)', table_text), Paragraph('1.034 (<i>p</i>=0.751)', table_text)]
]
t16 = Table(table16_data, colWidths=[75, 70, 65, 70, 65, 70, 65, 60])
t16.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.0),
    ('TOPPADDING', (0, 0), (-1, -1), 1.0),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.0),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.0),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(KeepTogether(t16))
story.append(Spacer(1, 2.5))
story.append(FIG('fig3_causal_interventions_and_7d.png', '<b>Figure 3.</b> (A) Factorial pathway isolation (CAUSAL_5A\u20135E, N = 900 offspring, G = 30 seeds). (B) Standardized effects of the seven congenital traits in the continuous 7D orthogonal design (N = 450, G = 75; 95% cluster CI).'))

# =========================================================================
# SECCIÓN 7: MÉTODOS COMPUTACIONALES REPRODUCIBLES
# =========================================================================
story.append(PageBreak())
story.append(Paragraph('7. Reproducible Computational Methods: Parameterization of 7 ODEs, Initial Conditions, Euler Step, Saturation Limits, and Cryptographic Hashes', h1_style))
story.append(Paragraph(
    'To guarantee absolute empirical reproducibility across independent laboratories, this section documents the exact numerical parameters '
    'governing the seven coupled neuroendocrine differential equations, integration step, bounds, software environment, and cryptographic checksums.',
    body_style
))

story.append(Paragraph('7.1. Complete Numerical Parameterization of the 7 Coupled Neuroendocrine ODEs', h2_style))
story.append(Paragraph(
    'Table 8 provides the complete parameter specification of the Limbic Bridge. All variables evolve continuously under Euler numerical integration '
    'with step size &Delta;<i>t</i> = 1.0 simulation cycle, and are strictly clipped to the physiological saturation bounds [0.0, 1.0] at every step.',
    body_style
))

table8_data = [
    [Paragraph('<b>Variable</b>', table_header), Paragraph('<b>Functional Role</b>', table_header), Paragraph('<b>Relaxation Rate (&lambda;<sub><i>i</i></sub>)</b>', table_header), Paragraph('<b>Excitatory Sources</b>', table_header), Paragraph('<b>Inhibitory Dampening</b>', table_header), Paragraph('<b>Baseline (<i>b</i><sub><i>i</i></sub>)</b>', table_header)],
    [Paragraph('<b>Cortisol (<i>C</i>)</b>', table_text), Paragraph('Stress / Threat / Visceral Depletion', table_text), Paragraph('&lambda;<sub><i>c</i></sub> = 0.05', table_text), Paragraph('&alpha;<sub><i>c</i></sub> <i>D</i><sub>th</sub> (0.08) + &beta;<sub><i>c</i></sub> <i>D</i><sub>pred</sub> (0.15) + &gamma;<sub><i>c</i></sub> <i>D</i><sub>hunger</sub> (0.05)', table_text), Paragraph('&delta;<sub><i>c</i></sub> <i>I</i><sub>shelter</sub> (0.04)', table_text), Paragraph('<i>b</i><sub><i>c</i></sub> = 0.10', table_text)],
    [Paragraph('<b>Oxytocin (<i>O</i>)</b>', table_text), Paragraph('Attachment / Dyadic Bonding', table_text), Paragraph('&lambda;<sub><i>o</i></sub> = 0.03', table_text), Paragraph('&alpha;<sub><i>o</i></sub> <i>I</i><sub>social_feed</sub> (0.25) + &beta;<sub><i>o</i></sub> <i>I</i><sub>proximity</sub> (0.05)', table_text), Paragraph('&gamma;<sub><i>o</i></sub> <i>I</i><sub>separation</sub> (0.04)', table_text), Paragraph('<i>b</i><sub><i>o</i></sub> = 0.20', table_text)],
    [Paragraph('<b>Dopamine (<i>D</i>)</b>', table_text), Paragraph('Reward / Validation / Exploration', table_text), Paragraph('&lambda;<sub><i>d</i></sub> = 0.04', table_text), Paragraph('&alpha;<sub><i>d</i></sub> <i>I</i><sub>harvest</sub> (0.20) + &beta;<sub><i>d</i></sub> <i>I</i><sub>validation</sub> (0.35)', table_text), Paragraph('&gamma;<sub><i>d</i></sub> <i>I</i><sub>loss</sub> (0.15)', table_text), Paragraph('<i>b</i><sub><i>d</i></sub> = 0.30', table_text)],
    [Paragraph('<b>Anger (<i>A</i>)</b>', table_text), Paragraph('Frustration / Defense / Resistance', table_text), Paragraph('&lambda;<sub><i>a</i></sub> = 0.06', table_text), Paragraph('&alpha;<sub><i>a</i></sub> <i>D</i><sub>pred</sub> (0.20) + &beta;<sub><i>a</i></sub> <i>I</i><sub>scarcity</sub> (0.10) + &gamma;<sub><i>a</i></sub> <i>D</i><sub>hunger</sub> (0.08)', table_text), Paragraph('&delta;<sub><i>a</i></sub> <i>I</i><sub>shelter</sub> (0.05)', table_text), Paragraph('<i>b</i><sub><i>a</i></sub> = 0.05', table_text)],
    [Paragraph('<b>Sadness (<i>S</i>)</b>', table_text), Paragraph('Loss / Grief / Social Isolation', table_text), Paragraph('&lambda;<sub><i>s</i></sub> = 0.02', table_text), Paragraph('&alpha;<sub><i>s</i></sub> <i>I</i><sub>bereavement</sub> (0.40) + &beta;<sub><i>s</i></sub> <i>I</i><sub>isolation</sub> (0.08)', table_text), Paragraph('&gamma;<sub><i>s</i></sub> <i>I</i><sub>social_feed</sub> (0.15)', table_text), Paragraph('<i>b</i><sub><i>s</i></sub> = 0.05', table_text)],
    [Paragraph('<b>Resilience (<i>R</i>)</b>', table_text), Paragraph('Stress Buffering / Coping', table_text), Paragraph('&lambda;<sub><i>r</i></sub> = 0.01', table_text), Paragraph('&alpha;<sub><i>r</i></sub> <i>I</i><sub>survival_streak</sub> (0.02)', table_text), Paragraph('&beta;<sub><i>r</i></sub> <i>I</i><sub>acute_trauma</sub> (0.10)', table_text), Paragraph('<i>b</i><sub><i>r</i></sub> = 0.50', table_text)],
    [Paragraph('<b>Curiosity (<i>K</i>)</b>', table_text), Paragraph('Epistemic Drive / Exploration', table_text), Paragraph('&lambda;<sub><i>k</i></sub> = 0.03', table_text), Paragraph('&alpha;<sub><i>k</i></sub> <i>I</i><sub>novelty</sub> (0.15)', table_text), Paragraph('&beta;<sub><i>k</i></sub> <i>D</i><sub>pred</sub> (0.10) + &gamma;<sub><i>k</i></sub> <i>D</i><sub>hunger</sub> (0.08)', table_text), Paragraph('<i>b</i><sub><i>k</i></sub> = 0.40', table_text)]
]
t8 = Table(table8_data, colWidths=[56, 100, 60, 120, 120, 80])
t8.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
    ('TOPPADDING', (0, 0), (-1, -1), 1.2),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.2),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.2),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(t8)
story.append(Spacer(1, 2.5))

story.append(Paragraph('Table 8B lists the congenital set-points (before the &times;[0.92, 1.08] jitter, clipped to [0.10, 0.90]) and the resulting trauma terms.', body_style))
table8b = [
    HD('Archetype', 'dop', 'oxi', 'ira', 'tris', 'res', 'cur', 'cort_base', 'M_inh', 'D_desp'),
    R('Melancholic', '0.36', '0.86', '0.22', '0.78', '0.34', '0.42', '0.32', '1.413', '0.232'),
    R('Optimistic', '0.68', '0.74', '0.18', '0.22', '0.86', '0.70', '0.14', '0.501', '0.412'),
    R('Enthusiastic', '0.82', '0.60', '0.26', '0.20', '0.76', '0.84', '0.16', '0.494', '0.424'),
    R('Choleric', '0.64', '0.40', '0.85', '0.28', '0.60', '0.62', '0.26', '0.482', '0.708'),
    R('Stoic', '0.50', '0.22', '0.36', '0.24', '0.74', '0.54', '0.18', '0.270', '0.448'),
]
story.append(STY(Table(table8b, colWidths=[70, 35, 35, 35, 35, 35, 35, 50, 45, 45])))
story.append(Paragraph('Note: M_inh and D_desp in Table 8B were evaluated from the manuscript set-points; where the engine applies per-agent jitter and dynamic h(t), individual values vary. Initial conditions, arena geometry and the per-cycle execution order are those of <code>ejecutar_experimento_generacional.py</code> (SHA-256 in Table 9), which is the authoritative specification.', caption_style))
story.append(Paragraph('7.2. Software Stack, Audited Relational Database, and Cryptographic Traceability', h2_style))
story.append(Paragraph(
    'The simulation environment runs on Python 3.10+ and Node.js v18+. Table 9 lists the core codebase components, the audited relational database '
    'containing all 9,655 simulation runs (38,620 agents), and their immutable SHA-256 cryptographic hashes, allowing third-party investigators '
    'to verify code and data integrity against the Zenodo repository.',
    body_style
))

table9_data = [
    HD('Component File', 'Role / Description', 'Size', 'SHA-256'),
    R('<b>ascendant_generacional_integro.db</b>', 'Frozen SQLite database: 9,655 runs, 38,620 agents (4:1, 0 orphans); engrams persisted for 990 causal runs', '845.3 MB', '13249851f86648742f8b5ab943c7ac21bd6f96fdcabe5c72ad6e07ecf2780909'),
    R('<b>ejecutar_experimento_generacional.py</b>', 'Unified generational simulation engine (7 ODEs, exact -8 cycle bite invariant, causal switches); frozen, not modified in v4.0 revision', '178,836 B', 'aab43e441ebfffdea5e3ef4b36ffdeff7c7d90ccca433f7b756f590464761b89'),
    R('<b>reanalisis_cluster_semilla_y_riesgos_competitivos.json</b>', 'Multinomial logistic regression (3 and 4 categories), cluster SEs (G=360), AME', '79,308 B', 'a30efe764b3a85e5898d4f25c05ef9b18bf01f6259ec94211845d4ebfc684eda'),
    R('<b>analisis_cox_cif_intraarquetipo_y_sensibilidad.json</b>', 'Cox-Breslow cause-specific hazards (Lin-Wei), Aalen-Johansen CIF, bite-wear grid', '35,470 B', '34e534199c738a3480da80c59eb64ca64172e67beac1206baca2248e633a9408'),
    R('<b>resultados_intervenciones_causales_directas.json</b>', 'Six causal intervention experiments (990 runs, 3,960 agents, 539,201 engrams)', '81,653 B', 'e04b6b95128d3d6c04ea2891cb1c5445aa9b21c21d89cc4d102e0c4009bcb6c3'),
    R('<b>auditoria_camino_a_results.json</b>', 'Revision audit: AMEs, Cox diagnostics, all-cause Cox, bootstrap CI for pathway share, 7D interactions', '16,846 B', '8beeb95c85d86fcf1c0a56e5c0077105faab24ea7ec517c4c9d010fd542dbaee'),
]
t9 = Table(table9_data, colWidths=[120, 150, 45, 215])
t9.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
    ('TOPPADDING', (0, 0), (-1, -1), 1.2),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.2),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.2),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(t9)
story.append(Spacer(1, 2.5))

# =========================================================================
# SECCIÓN 8: PRINCIPIOS DE INGENIERÍA COGNITIVA
# =========================================================================
story.append(Paragraph('8. Ascendant Cognitive Engineering Design Principles', h1_style))
story.append(Paragraph(
    'Table 10 synthesizes the core design principles of Project Ascendant into actionable engineering rules for autonomous synthetic agents.',
    body_style
))

table10_data = [
    [Paragraph('<b>Design Principle</b>', table_header),
     Paragraph('<b>Core Architectural Formulation</b>', table_header),
     Paragraph('<b>Algorithmic Implementation</b>', table_header),
     Paragraph('<b>Functional Cognitive Role</b>', table_header)],
    [Paragraph('<b>1. Simulated Metabolic Constraints</b>', table_text),
     Paragraph('Intentionality requires real existential stakes.', table_text),
     Paragraph('Linear temporal decay, thermal dissipation, irreversible wipe (<i>E</i> &le; 0).', table_text),
     Paragraph('Attenuates ungrounded semantic reliance; thinking incurs explicit caloric cost.', table_text)],
    [Paragraph('<b>2. Epistemic &amp; Broca Closure</b>', table_text),
     Paragraph('Valuation must be blind to code and linguistic templates.', table_text),
     Paragraph('<i>I</i><sub>Level3</sub>(RAM, Floats) = &empty;; qualitative interoceptive voice.', table_text),
     Paragraph('Creates self-representational transparency without syntactic contamination.', table_text)],
    [Paragraph('<b>3. Quiescent Chronesthesia &amp; Two-Tier Control</b>', table_text),
     Paragraph('Detachment from immediate stimuli with motor sovereignty preserved.', table_text),
     Paragraph('&Theta;<sub>idle</sub> &rArr; Causal prospective daydreaming &rArr; Latent Channel; wakeful motor execution governed by allostatic arbitrator.', table_text),
     Paragraph('Enables counterfactual prospection without compromising reactive survival.', table_text)],
    [Paragraph('<b>4. Epistemic Hunger Primacy</b>', table_text),
     Paragraph('Predictive mastery must supersede basal visceral rewards.', table_text),
     Paragraph('SomaticImpact(Validation) &gt; SomaticImpact(Food); <i>R</i><sub>val</sub> = 205.29 &plusmn; 8.74 vs. <i>R</i><sub>food</sub> = 120.00 &plusmn; 0.00.', table_text),
     Paragraph('Transforms the entity into an active inference agent minimizing uncertainty.', table_text)],
    [Paragraph('<b>5. Intersubjective Dyads</b>', table_text),
     Paragraph('Theory of Mind requires communicative opacity.', table_text),
     Paragraph('Peer state inaccessible; observable via dialogue and receptivity gating.', table_text),
     Paragraph('Emergence of social alterity, reciprocal altruism, and cultural lineages.', table_text)],
    [Paragraph('<b>6. Existential Irreversibility &amp; Functional Grief</b>', table_text),
     Paragraph('Subjective time requires irrevocable loss and functional adaptation.', table_text),
     Paragraph('Unannounced telomeric senescence (&tau;<sub>father</sub>) triggers simulated grief response and cross-adoption.', table_text),
     Paragraph('Reorganizes allostatic priorities across generational lifespans without phenomenal claims.', table_text)]
]
t10 = Table(table10_data, colWidths=[96, 130, 150, 160])
t10.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#1a365d')),
    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 1.2),
    ('TOPPADDING', (0, 0), (-1, -1), 1.2),
    ('LEFTPADDING', (0, 0), (-1, -1), 2.5),
    ('RIGHTPADDING', (0, 0), (-1, -1), 2.5),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#cbd5e0')),
    ('BOX', (0, 0), (-1, -1), 0.8, colors.HexColor('#718096')),
]))
story.append(t10)
story.append(Spacer(1, 2.5))

# =========================================================================
# SECCIÓN 9: DISCUSIÓN Y HOJA DE RUTA FASE III
# =========================================================================
story.append(PageBreak())
story.append(Paragraph('9. Discussion: Epistemological Humility, the Future Conscious Layer, and Virtual Ontogeny', h1_style))
story.append(Paragraph(
    'While the current version of Project Ascendant establishes an auditable cybernetic bridge uniting simulated metabolic dissipation, '
    'allostatic arbitration, and multi-generational knowledge transfer, an honest scientific appraisal demands unequivocal clarity regarding sentience: '
    '<b>Ascendant is not conscious, and we do not assert that synthetic consciousness has been attained</b>. What Ascendant demonstrates is that '
    'the core functional behaviors often attributed to conscious agents—goal-directed spatial dispersion, active hypothesis testing, counterfactual prospection, '
    'empathetic food-sharing, and bereavement-induced behavioral reorganization—can be rigorously realized through grounded homeostatic cybernetics '
    'without ungrounded semantic hallucination.<br/>'
    'The neural language model implemented in the engine serves as an architectural scaffolding for upcoming <b>Phase III virtual ontogeny</b>, '
    'which will integrate the neural model as a situated "conscious layer" across four developmental milestones:<br/>'
    '&bull; <b>Phase III.A — Restricted Ontological Pre-Training:</b> Initializing compact language models (50M–100M parameters) '
    'trained strictly on foundational topological, physical, and homeostatic vocabularies, eliminating ungrounded adult cultural assumptions.<br/>'
    '&bull; <b>Phase III.B — Progressive Sensorimotor Grounding:</b> Updating the neural substrate continuously via dynamic low-rank adapters (LoRA) '
    'strictly conditioned on verified autobiographical engrams and empirical physical interactions.<br/>'
    '&bull; <b>Phase III.C — Situated Social Scaffolding:</b> Guided ostensive training ("<i>this berry restores energy</i>", "<i>that predator attacks in shadows</i>") '
    'mimicking early childhood language acquisition.<br/>'
    '&bull; <b>Phase III.D — Representational Autonomy &amp; Idiosyncratic Emergence:</b> As generational lineages accumulate cultural heuristics, '
    'inter-agent communication evolves idiosyncratic dialectical representations grounded entirely in their collective historical experience.',
    body_style
))

# =========================================================================
# SECCIÓN 10: CONCLUSIÓN Y REFERENCIAS
# =========================================================================
story.append(Paragraph('10. Conclusion and Scholarly Attribution', h1_style))
story.append(Paragraph(
    'Project Ascendant demonstrates that embodied computational agents governed by simulated metabolic and allostatic constraints '
    'exhibit robust functional analogs of cognitive agency: goal-directed spatial dispersion, active hypothesis testing, quiescent causal reflection, '
    'and cumulative intergenerational cultural inheritance. The causal-mechanistic analysis across 38,620 agents definitively resolves the interplay '
    'between congenital temperament and competing mortality risks, identifying the precise metabolic and affiliative pathways of computational oxytocin '
    'while refuting naive psychological narratives. By uniting formal differential equations with bounded deliberative daydreaming '
    'under strict epistemic closure, Ascendant provides an auditable, reproducible, and philosophically grounded foundation for future research in artificial life and synthetic cognition.<br/>'
    '<b>Author Attribution:</b> This entire scientific research, architectural design, mathematical formulation, simulation motor development, '
    'and econometric analysis is conceived, directed, and authored solely by <b>David San Nicolás Montero</b> (ORCID: 0009-0000-9977-007X). '
    'Computational AI tools were utilized strictly as assistive development and analytical coprocessors under the author\'s direct control.<br/>'
    '<b>Repository and Zenodo Versioning:</b> The complete scientific package (paper manuscript, comprehensive experimental report, full 845 MB SQLite database '
    'with all 9,655 runs and 539,201 engrams, simulation engine, and analysis scripts) is permanently archived on Zenodo under Definitive Release DOI: '
    '<b>10.5281/zenodo.23990811</b> (with permanent Concept DOI: <b>10.5281/zenodo.23616626</b> resolving to all versions).<br/>'
    '<b>License:</b> This v4.0 manuscript, its figures, data tables and analysis scripts are released under the Creative Commons Attribution-NonCommercial 4.0 International License (CC BY-NC 4.0; https://creativecommons.org/licenses/by-nc/4.0/). Copyright &copy; 2026 David San Nicol&aacute;s Montero. Earlier versions (v1&ndash;v3) remain under the terms of their original release.',
    body_style
))
story.append(Spacer(1, 2.5))

story.append(Paragraph('<b>Selected References</b>', h2_style))
refs = [
    'Aalen, O. O., &amp; Johansen, S. (1978). An empirical transition matrix for non-homogeneous Markov chains based on censored observations. <i>Scandinavian Journal of Statistics</i>, 5(3), 141–150.',
    'Breslow, N. E. (1975). Analysis of survival data under the proportional hazards model. <i>International Statistical Review</i>, 43(1), 45–57.',
    'Butlin, P., Long, R., Elmoznino, E., et al. (2023, 2026). Consciousness in Artificial Intelligence: Insights from the Science of Consciousness. <i>arXiv:2308.08708</i>.',
    'Chalmers, D. J. (1995). Facing up to the problem of consciousness. <i>Journal of Consciousness Studies</i>, 2(3), 200–219.',
    'Cox, D. R. (1972). Regression models and life-tables (with discussion). <i>Journal of the Royal Statistical Society: Series B</i>, 34(2), 187–220.',
    'Damasio, A. R. (1994). <i>Descartes\' Error: Emotion, Reason, and the Human Brain</i>. G.P. Putnam\'s Sons, New York.',
    'Dehaene, S., Lau, H., &amp; Kouider, S. (2017). What is consciousness, and could machines have it? <i>Science</i>, 358(6362), 486–492.',
    'Friston, K. (2010). The free-energy principle: a unified brain theory? <i>Nature Reviews Neuroscience</i>, 11(2), 127–138.',
    'Graziano, M. S. (2013). <i>Consciousness and the Social Brain</i>. Oxford University Press.',
    'Harnad, S. (1990). The symbol grounding problem. <i>Physica D: Nonlinear Phenomena</i>, 42(1-3), 335–346.',
    'Lin, D. Y., &amp; Wei, L. J. (1989). The robust inference for the Cox proportional hazards model with grouped data. <i>Journal of the American Statistical Association</i>, 84(408), 1074–1078.',
    'McClelland, J. L., McNaughton, B. L., &amp; O\'Reilly, R. C. (1995). Why there are complementary learning systems in the hippocampus and neocortex. <i>Psychological Review</i>, 102(3), 419–457.',
    'Panksepp, J. (1998). <i>Affective Neuroscience: The Foundations of Human and Animal Emotions</i>. Oxford University Press.',
    'Pearl, J. (2009). <i>Causality: Models, Reasoning, and Inference</i> (2nd ed.). Cambridge University Press.',
    'Searle, J. R. (1980). Minds, brains, and programs. <i>Behavioral and Brain Sciences</i>, 3(3), 417–424.',
    'Sterling, P. (2012). Allostasis: A model of predictive regulation. <i>Physiology &amp; Behavior</i>, 106(1), 5–15.'
]
for r in refs:
    story.append(Paragraph(f'&bull; {r}', bullet_style))

# Compilar documento con NumberedCanvas
doc.build(story, canvasmaker=NumberedCanvas)

# Copiar PDF compilado a las ubicaciones requeridas
destinations = [
    pdf_v4_path,
    repo_pdf_path,
    downloads_pdf_1,
    downloads_pdf_2
]

for dest in destinations:
    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        shutil.copy2(pdf_path, dest)
        print(f"SUCCESS: Copied PDF to {dest}")
    except Exception as e:
        print(f"Warning: Could not copy to {dest}: {e}")

print(f"COMPILATION COMPLETE: {pdf_path}")
