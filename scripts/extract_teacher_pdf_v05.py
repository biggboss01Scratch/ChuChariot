"""Rebuild the fifth candidate batch from the checked, page-addressable excerpts.

This is a deterministic curation pass, not an autonomous OCR/LLM extractor.
The original PDF remains the primary source; ambiguous readings are excluded.
"""

from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

from chuchariot.validation import validate

ROOT = Path(__file__).resolve().parents[1]
RUN = 'run:20261123-teacher-pdf'


def build():
    base_path = ROOT / 'data/candidates/wheel-axle.v0.4.json'
    data = json.loads(base_path.read_text(encoding='utf-8'))
    checked = json.loads((ROOT / 'data/extractions/teacher-pdf-pass.v0.1.json').read_text(encoding='utf-8'))
    original = ROOT.parent / next(s['filename'] for s in data['sources'] if s['id'] == 'source:001')
    if original.exists():
        assert hashlib.sha256(original.read_bytes()).hexdigest() == checked['source_sha256'], 'Source PDF changed; recheck excerpts.'
    ontology = json.loads((ROOT / 'data/ontology/ontology.v0.2.json').read_text(encoding='utf-8'))
    ontology['version'] = '0.3.0'
    ontology['entity_kinds']['ReferenceRecord'] = '来源中的未编号对象、统计或复原图记录，不等于主展品实物'
    ontology['entity_kinds']['HarnessRole'] = '图示中的系驾角色，不是某匹已识别的实物马'
    predicates = ontology['predicates']
    predicates['REFERS_TO_TYPE'] = {'label': '来源记录涉及部件类别', 'object_kind': 'entity', 'endpoint_pairs': [['ReferenceRecord', 'ComponentType']]}
    predicates['DEPICTS'] = {'label': '来源图示呈现对象或概念', 'object_kind': 'entity', 'endpoint_pairs': [['ReferenceRecord', k] for k in ['ComponentType', 'Chariot', 'HarnessRole']]}
    predicates['TENON_JOINT_WITH'] = {'label': '榫卯相接', 'object_kind': 'entity', 'endpoint_pairs': [['Component', 'Component']]}
    predicates['HAS_ASSOCIATED_COMPONENT'] = {'label': '所配部件', 'object_kind': 'entity', 'endpoint_pairs': [['ReferenceSpecimen', 'Component']]}
    predicates['HAS_MEASUREMENT']['endpoint_pairs'].append(['ReferenceRecord', 'Measurement'])
    for predicate in ['HAS_MATERIAL', 'HAS_PRESERVED_FEATURE', 'HAS_SURFACE_FINISH', 'HAS_DECORATION_MOTIF']:
        target = predicates[predicate]['endpoint_pairs'][0][1]
        predicates[predicate]['endpoint_pairs'].append(['ReferenceRecord', target])
    predicates['DESCRIPTION']['subject_kinds'].extend(['ReferenceRecord', 'HarnessRole'])
    for key, label in {
        'HAS_SHAPE': '形态与结构特征', 'HAS_PROCESSING': '加工与制作记载',
        'HAS_POSITION': '位置记载', 'HAS_FIND_POSITION': '出土位置',
        'HAS_RECORDED_QUANTITY': '原文数量', 'HAS_MASS_RECORD': '原文重量记录',
        'HAS_ORIGINAL_IDENTIFIERS': '原文标识范围', 'HAS_DIAGRAM_LABELS': '图内标注',
        'HAS_PATTERN_DETAIL': '纹饰部位与细节',
    }.items():
        predicates[key] = {'label': label, 'object_kind': 'text',
                           'subject_kinds': ['Component', 'ReferenceSpecimen', 'ReferenceRecord']}

    data['ontology_version'] = ontology['version']
    data['dataset_id'] = 'dataset:teacher-pdf-005'
    data['description'] = '第五批：继承v0.4，逐页补提教师汇编中的部件、标本、尺寸、形态、连接、工艺及图示记录；全部新增事实待审核，复原图与实物记录分开。'
    old_counts = {k: len(data[k]) for k in ['entities', 'facts', 'evidence', 'model_mappings']}
    entities = {e['id']: e for e in data['entities']}
    evidence_by_key = {}
    coverage = {}
    added = []
    fact_counter = measurement_counter = 0

    def entity(ident, kind, label, aliases=(), **extra):
        if ident in entities:
            raise ValueError(f'duplicate entity {ident}')
        record = {'id': ident, 'kind': kind, 'label': label, 'aliases': list(aliases), **extra}
        data['entities'].append(record)
        entities[ident] = record
        return ident

    def evidence(key, scope='', figure=False):
        if key in evidence_by_key:
            return evidence_by_key[key]
        row = checked['figures' if figure else 'paragraphs'][key]
        quote = row['caption'] + ' 图内文字：' + row['labels'] if figure else row['quote']
        ident = 'evidence:pdf-' + key.lower()
        note = '直接来源为教师汇编，非原始发掘报告；不自动归属于九连墩六号车。'
        if '？' in quote:
            note += ' 引文含转写疑读标记，本批事实不采用这些疑读字词。'
        note += ' ' + scope
        data['evidence'].append({'id': ident, 'source_id': 'source:001', 'pdf_page': row['pdf_page'],
                                 'locator': f'原PDF第{row["pdf_page"]}页：' + row.get('section', row.get('title', '')) + f'；转写定位{key}',
                                 'quote': quote, 'transcription': 'image_transcription',
                                 'check_status': 'source_checked', 'scope_note': note.strip()})
        evidence_by_key[key] = ident
        coverage[key] = {'pdf_page': row['pdf_page'], 'fact_ids': [], 'excluded': []}
        return ident

    def fact(subject, predicate, target, key, *, text=False, origin='documented', rationale=None):
        nonlocal fact_counter
        evid = evidence_by_key.get(key) or evidence(key, figure=key.startswith('figure-'))
        fact_counter += 1
        ident = f'fact:pdf-{fact_counter:03}'
        item = {'id': ident, 'subject_id': subject, 'predicate': predicate,
                'value' if text else 'object_id': target, 'evidence_ids': [evid],
                'origin': origin, 'review_status': 'pending',
                'extraction': {'method': 'checked_pdf_atomic_extraction', 'run_id': RUN}}
        if rationale:
            item['rationale'] = rationale
        data['facts'].append(item)
        coverage[key]['fact_ids'].append(ident)
        added.append(ident)
        return ident

    def literal(subject, predicate, value, key, **extra):
        return fact(subject, predicate, value, key, text=True, **extra)

    def description(subject, value, key):
        return literal(subject, 'DESCRIPTION', value, key)

    def measurement(owner, quantity, value, key, *, approximate=False):
        nonlocal measurement_counter
        measurement_counter += 1
        ident = f'measurement:pdf-{measurement_counter:03}'
        raw = checked['paragraphs'][key]['quote']
        raw_by_passage = {
            'P01-T03':'通宽49、高52厘米',
            'P01-T05':'可见部分长163、宽约1.5厘米',
            'P01-T07':'可见部分长177、宽约3厘米',
            'P02-T01':'衡残长136、宽4.2、厚3.6厘米',
            'P03-T01':'残长39.6、前宽7.6、最高7.6、身前宽4、高5.2厘米',
            'P04-T04':'轴通长272、粗径9.7、细径2.6厘米',
            'P05-T02':'口径6.1、末端径3.4、通长8、辖长6.15厘米',
        }
        raw = raw_by_passage.get(key, raw)
        if key == 'P02-T02':
            raw = '辀长328、厚3.1厘米'
            if '处宽' in quantity: raw = '辀在前轸处较宽，宽13厘米，近衡处较窄，宽6厘米'
            if '外露' in quantity: raw = '外露部分长4.5、宽7.3、厚4.2厘米'
        if key == 'P04-T02':
            raw = '轴通长276、粗径5、细径3.5厘米' if value != 2 else '轴置于舆下的中轴经线前2厘米处'
        if key == 'P06-T01':
            for owner_suffix, excerpt in {
                'ch15-rim':'牙高6.7、宽4.6厘米',
                'ch15-spoke':'辐通长50厘米',
                'ch15-spoke-inner':'内段为股，与毂榫卯结合，横截面扁棱形，宽4.4、厚1.4厘米',
                'ch15-spoke-outer':'外段为骹，与轮牙榫卯结合，横截面圆柱形，直径2.9厘米',
                'ch15-hub':'毂通长70、贤端径13.5、壶中径17、轵端径6厘米',
                'ch15-hub-ridges':'篆间隔1.6、宽0.8、高0.4~0.6厘米',
                'ch15-wood-strips':'木条长118、径3厘米',
                'ch15-binding':'皮条宽1.5厘米',
            }.items():
                if owner == 'component:' + owner_suffix: raw = excerpt
        if key == 'P07-T02':
            raw = '通长22.5厘米，重220克' if quantity == '通长' else '镳长37厘米'
            if '浇痕' in quantity: raw = '痕长1.4、宽0.3厘米'
        record = {'quantity': quantity, 'unit': 'cm', 'raw': raw, 'approximate': approximate}
        if isinstance(value, tuple): record.update(min=value[0], max=value[1])
        else: record['value'] = value
        entity(ident, 'Measurement', entities[owner]['label'] + ' · ' + quantity, scope_id=owner, measurement=record)
        fact(owner, 'HAS_MEASUREMENT', ident, key)
        return ident

    def dimensions(owner, rows, key):
        for quantity, value in rows:
            measurement(owner, quantity, value, key)

    def category(slug, label, key, *, aliases=(), note=None):
        ident = entity('type:' + slug, 'ComponentType', label, aliases, **({'note': note} if note else {}))
        return ident

    def specimen(slug, label, kind, key, aliases=(), note=None):
        ident = entity('specimen:' + slug, 'ReferenceSpecimen', label, aliases, note=note or '按汇编中具名标本登记；与六号车的实物归属未核实。')
        fact(ident, 'INSTANCE_OF', kind, key)
        return ident

    def source_record(slug, label, kind, key, note):
        ident = entity('record:' + slug, 'ReferenceRecord', label, note=note)
        if kind:
            fact(ident, 'REFERS_TO_TYPE', kind, key)
        return ident

    def component(slug, label, owner, kind, key, *, parent=None, associated=False, note=None):
        ident = entity('component:' + slug, 'Component', label, scope_id=owner,
                       **({'note': note} if note else {}))
        fact(parent or owner, 'HAS_ASSOCIATED_COMPONENT' if associated else 'HAS_PART', ident, key)
        if kind:
            fact(ident, 'INSTANCE_OF', kind, key)
        return ident

    # Categories are grounded in headings or explicit labels, including terms
    # whose chapter has only a heading. No absent content is fabricated.
    yoke = category('yoke', '轭', 'P01-T03', aliases=['軛'])
    trace = category('trace', '靷', 'P01-T04')
    beam = category('beam', '衡', 'P02-T01')
    yi = category('yi', '轙', 'P02-T01', note='原文称四轙长方形；与第8页“轙环”不未经核实合并。')
    beamcap = category('beam-cap', '骨衡帽', 'P02-T01')
    pole = category('pole', '辀', 'P02-T02', aliases=['輈'])
    polehead = category('pole-head', '辀首', 'P03-T01')
    body = category('body', '舆', 'figure-18', aliases=['輿'])
    futu = category('futu', '伏兔', 'figure-09')
    inner = category('spoke-inner', '股', 'P06-T01', note='这里指辐的内段，不采用同字的其他词义。')
    outer = category('spoke-outer', '骹', 'P06-T01', note='这里指辐的外段。')
    zhuan = category('hub-ridge', '篆', 'P06-T01', note='本页指毂轵部环棱状窄篆，不与文字书体概念合并。')
    strip = category('wheel-strip', '车轮附加圆木条', 'P06-T01')
    leatherstrip = category('binding-strip', '捆扎皮条', 'P06-T01')
    bit = category('bit', '衔', 'P07-T02')
    cheek = category('cheekpiece', '镳', 'P07-T02')
    bridle = category('bridle', '辔', 'figure-16', note='原页小节名为“辔”，所附图题为马勒推测复原图；本批保留图题性质。')
    reins = category('reins', '缰', 'figure-17')
    yiring = category('yi-ring', '轙环', 'figure-17')
    youring = category('you-ring', '游环', 'figure-17')
    buckle = category('buckle', '节约', 'figure-15')
    railing = category('railing', '围栏', 'figure-18')
    for slug, label in [('floor-mat','车茵'), ('body-cover','车蔽衣'), ('umbrella','伞'), ('canopy','盖')]:
        ident = entity('type:' + slug, 'ComponentType', label, note='原第9页只有小节标题，无属性、实例或六号车归属的正文证据。')
        # A separate evidence record retains the heading, not invented content.
        key = 'heading-p09-' + slug
        checked['paragraphs'][key] = {'pdf_page': 9, 'section': '四、舆，后两小节标题', 'quote': '（二）车茵、车蔽衣；（三）伞、盖'}
        description(ident, f'原第9页标题列出“{label}”，该小节无展开内容。', key)

    hemp = entity('material:hemp-or-silk', 'Material', '麻或丝（原文未定）', ['麻（或丝）'], note='保留原文二选一的不确定性，不拆成两条肯定材质事实。')
    hide = entity('material:hide', 'Material', '皮质', ['皮'])
    bone = entity('material:bone', 'Material', '骨质', ['骨'])
    charred = entity('preservation:charred-trace', 'PreservationFeature', '炭化后仅存深褐色痕迹', ['已炭化，仅存痕迹'])
    painttrace = entity('preservation:brown-paint-trace', 'PreservationFeature', '残留少量深褐色漆痕迹')
    ribbon = entity('motif:ribbon', 'DecorationMotif', '带纹')

    # Original PDF page 1: yoke and two distinct traces; statistics are records.
    sy = specimen('ch13-yoke', 'CH1：3轭标本', yoke, 'P01-T03', ['CH1:3轭'], '与既有 CH1：3轴标本分开登记；同号不等于同一对象。')
    for pred, target in [('HAS_MATERIAL','material:001'), ('HAS_PRESERVED_FEATURE','preservation:001'), ('HAS_SURFACE_FINISH','finish:001')]:
        fact(sy, pred, target, 'P01-T03')
    dimensions(sy, [('通宽',49),('高',52)], 'P01-T03')
    for slug, label, key, material, length, width in [('ch11-trace','CH1：1靷标本','P01-T05',hemp,163,1.5), ('ch14-trace','CH1：4靷标本','P01-T07',hide,177,3)]:
        st = specimen(slug,label,trace,key)
        fact(st,'HAS_MATERIAL',material,key)
        fact(st,'HAS_PRESERVED_FEATURE',charred,key)
        fact(st,'HAS_PRESERVED_FEATURE',painttrace,key)
        measurement(st,'可见部分长',length,key)
        measurement(st,'宽',width,key,approximate=True)
        if slug=='ch11-trace':
            literal(st,'HAS_PROCESSING','三根合并对折而成',key)
            literal(st,'HAS_SHAPE','分成左右两股，前端结小套环',key)
        else:
            literal(st,'HAS_SHAPE','前端小套环，后端大套环',key)
            literal(st,'HAS_POSITION','从前轸下引出双股，由辀的两侧前引至左右服马后脊处',key)
    for slug,label,key,count,ids in [('hemp-trace-count','麻或丝靷统计记录','P01-T04','5根','CH1：1、6、12、14、22'),('hide-trace-count','皮靷统计记录','P01-T06','14根','CH1：2~5、7~10、13、15、16、20、24、33')]:
        rec=source_record(slug,label,trace,key,'表九六及正文的统计集合，不是单件标本，数量不属于六号车。')
        literal(rec,'HAS_RECORDED_QUANTITY',count,key)
        literal(rec,'HAS_ORIGINAL_IDENTIFIERS',ids,key)

    # Page 2: numbered beam and unnumbered pole paragraph stay separate.
    sb = specimen('ch14-beam','CH1：4衡标本',beam,'P02-T01',['CH1:4衡'],'与同号 CH1：4靷分开。残长不当作完整长度。')
    fact(sb,'HAS_MATERIAL','material:001','P02-T01')
    fact(sb,'HAS_PRESERVED_FEATURE','preservation:001','P02-T01')
    for shape in ['波浪形，中粗两端细','横截面扁方形']:
        literal(sb,'HAS_SHAPE',shape,'P02-T01')
    dimensions(sb,[('残长',136),('宽',4.2),('厚',3.6)],'P02-T01')
    by=component('ch14-yi','CH1：4衡的轙（合组记录）',sb,yi,'P02-T01')
    literal(by,'HAS_RECORDED_QUANTITY','4个','P02-T01')
    literal(by,'HAS_SHAPE','长方形','P02-T01')
    bc=component('ch14-beam-caps','CH1：4衡两端骨衡帽',sb,beamcap,'P02-T01')
    fact(bc,'HAS_MATERIAL',bone,'P02-T01')
    literal(bc,'HAS_POSITION','套于衡两端','P02-T01')
    up=source_record('p02-unnumbered-pole','第2页未编号辀记录',pole,'P02-T02','原段无明确标本号；保留记录对象，不归给 M1：302 残件或六号车。')
    dimensions(up,[('长',328),('厚',3.1),('前轸处宽',13),('近衡处宽',6),('踵外露部分长',4.5),('踵外露部分宽',7.3),('踵外露部分厚',4.2)],'P02-T02')
    literal(up,'HAS_SHAPE','前端上扬，后段贴于地面；横截面扁方形','P02-T02')
    literal(up,'HAS_POSITION','纵向置于舆下轴上中轴纬线上；踵露于轮后（原文用语照录）','P02-T02')

    # Page 3: pole fragment. Local lacquer is tied to regions, not generalized.
    fact('specimen:004','INSTANCE_OF',pole,'P03-T01')
    literal('specimen:004','HAS_FIND_POSITION','南室第二层西部中间靠西壁处','P03-T01')
    front_fragment=entity('preservation:front-fragment','PreservationFeature','残存前段')
    fact('specimen:004','HAS_PRESERVED_FEATURE',front_fragment,'P03-T01')
    literal('specimen:004','HAS_SHAPE','辀身长方体，前粗后细','P03-T01')
    dimensions('specimen:004',[('残长',39.6),('前宽',7.6),('最高',7.6),('身前宽',4),('身前高',5.2)],'P03-T01')
    ph=component('m1302-head','M1：302辀首','specimen:004',polehead,'P03-T01')
    for shape in ['前上部中间有长方形穿孔','下部成“凹”字形','后部横穿圆孔']:
        literal(ph,'HAS_SHAPE',shape,'P03-T01')
    fact(ph,'HAS_SURFACE_FINISH','finish:001','P03-T01')
    for slug,label,finish in [('front','前段','finish:001'),('middle','中段','finish:002'),('rear','后段','finish:002')]:
        part=component('m1302-'+slug,'M1：302辀身'+label,'specimen:004',None,'P03-T01',note='原文描述的区域，不代表可拆卸零件。')
        fact(part,'HAS_SURFACE_FINISH',finish,'P03-T01')
        if slug=='rear':
            literal(part,'HAS_PATTERN_DETAIL','黑漆上有一周红漆','P03-T01')

    # Page 4: unknown record and CH1:3 reference cannot share measurements.
    ua=source_record('p04-unnumbered-axle','第4页未编号轴记录','type:002','P04-T02','位于“参考”之前的独立段落；不得与 CH1：3参考轴标本混合。')
    dimensions(ua,[('通长',276),('粗径',5),('细径',3.5),('相对舆中轴经线向前距离',2)],'P04-T02')
    literal(ua,'HAS_SHAPE','长条形，横截面下圆上方，末端锥形贯毂','P04-T02')
    literal(ua,'HAS_POSITION','位于舆下的中轴经线前2厘米处','P04-T02')
    axis_count=source_record('p04-axle-count','第4页轴数量记录','type:002','P04-T03','原文整体统计，不是六号车车轴数量。')
    literal(axis_count,'HAS_RECORDED_QUANTITY','登记33件；现存22件','P04-T03')
    dimensions('specimen:002',[('粗径',9.7),('细径',2.6)],'P04-T04')
    literal('specimen:002','HAS_PROCESSING','一根整木砍刨打磨光滑而成','P04-T04')
    literal('specimen:002','HAS_SHAPE','中部较粗，贯毂部分内粗外细，呈圆锥体','P04-T04')
    literal('specimen:002','HAS_SHAPE','轴上部应为平面，下部为圆弧形（原文推测）','P04-T04',origin='inferred',rationale='汇编根据轴与伏兔的连接推测截面；不是本轮新增实测或已确认的考古结论。')
    literal('specimen:002','HAS_SHAPE','末端有长方形榫钉孔，套軎后辖插入其中','P04-T04')
    # The sequence is retained as a statement, not a full assembly dependency.
    description(futu,'汇编在轴的参考段中讨论轴与伏兔的连接；部件图另标“伏兔”。','P04-T04')

    # Page 5: the artifact, its associated pin, mass and decoration.
    cap_group=source_record('p05-cap-pair','双箍云纹圆筒形车軎组记录','type:006','P05-T01','本段为器物组统计，不是所有车軎或六号车数量。')
    literal(cap_group,'HAS_RECORDED_QUANTITY','2件，1对','P05-T01')
    literal(cap_group,'HAS_FIND_POSITION','南室第一层东段中部偏南处','P05-T01')
    for shape in ['末端平，正中有小圆孔；首端口部斜折，宽沿方唇','双凸箍，箍下有垫片','外箍一侧下伸长嘴鸟首形钩；内箍与口部间有对称长方形穿']:
        literal(cap_group,'HAS_SHAPE',shape,'P05-T01')
    literal(cap_group,'HAS_PROCESSING','鸟首形钩范线痕被原文解释为双范合铸、嵌入軎体叠铸的依据','P05-T01',origin='inferred',rationale='原文依据范线痕解释铸造方式；保留其推断性质，不作为本轮独立实验结论。')
    literal(cap_group,'HAS_PATTERN_DETAIL','通体错金银带纹和勾连云纹；末端面四蒂状卷云纹；双箍外壁勾连云纹；箍间四组方块夹对三角勾连云纹','P05-T01')
    dimensions('specimen:003',[('口径',6.1),('末端径',3.4),('通长',8)],'P05-T02')
    literal('specimen:003','HAS_MASS_RECORD','原文记重470克；是否包含所配辖未另行注明','P05-T02')
    for shape in ['末端圆形，顶中央圆形穿孔','近两端各有一道圆凸箍','近顶圆箍上侈出鸟首饰物，长变形喙','另一圆箍至沿之间有对称的两个长方形穿孔','宽直沿，沿内侧呈斜坡形']:
        literal('specimen:003','HAS_SHAPE',shape,'P05-T02')
    literal('specimen:003','HAS_PROCESSING','通体错金银；器身经不同程度锉磨加工','P05-T02')
    literal('specimen:003','HAS_PATTERN_DETAIL','箍上均有三道凹弦纹；鸟首下颈至喙端有明显范线痕','P05-T02')
    fact('specimen:003','HAS_DECORATION_MOTIF',ribbon,'P05-T02')
    fact('specimen:003','HAS_DECORATION_MOTIF','motif:001','P05-T02')
    pin=component('m1201-pin','M1：201-1车軎所配辖','specimen:003','type:007','P05-T02',associated=True,note='原文“軎上贯一件辖”；所配不等于軎体自身材料或纹饰。')
    measurement(pin,'长',6.15,'P05-T02')
    literal(pin,'HAS_SHAPE','兽面辖首，辖身长方条形；末端长方形横穿，顶有近方形浅痕','P05-T02')
    literal(pin,'HAS_PROCESSING','器身有锉磨加工痕','P05-T02')

    # Page 6: break the wheel description into scoped components and dimensions.
    rim=component('ch15-rim','CH1：5轮牙','specimen:001','type:005','P06-T01')
    spoke=component('ch15-spoke','CH1：5轮辐（尺寸记录对象）','specimen:001','type:004','P06-T01',note='用于承接原文辐的尺寸，不据示意图补辐数或指定某一根。')
    hub=component('ch15-hub','CH1：5轮毂','specimen:001','type:003','P06-T01')
    for shape in ['截面略呈梯形','着地面和两侧略鼓']:
        literal(rim,'HAS_SHAPE',shape,'P06-T01')
    dimensions(rim,[('牙高',6.7),('牙宽',4.6)],'P06-T01')
    measurement(spoke,'通长',50,'P06-T01')
    si=component('ch15-spoke-inner','CH1：5轮辐内段（股）','specimen:001',inner,'P06-T01',parent=spoke)
    so=component('ch15-spoke-outer','CH1：5轮辐外段（骹）','specimen:001',outer,'P06-T01',parent=spoke)
    literal(si,'HAS_SHAPE','横截面扁棱形','P06-T01')
    literal(so,'HAS_SHAPE','横截面圆柱形','P06-T01')
    dimensions(si,[('宽',4.4),('厚',1.4)],'P06-T01')
    measurement(so,'直径',2.9,'P06-T01')
    literal(spoke,'HAS_SHAPE','骹与股过渡较平滑，无明显界线；骹长于股','P06-T01')
    fact(si,'TENON_JOINT_WITH',hub,'P06-T01')
    fact(so,'TENON_JOINT_WITH',rim,'P06-T01')
    literal(hub,'HAS_SHAPE','圆锥状，近贤端较粗，呈圆鼓腹，中空','P06-T01')
    dimensions(hub,[('通长',70),('贤端径',13.5),('壶中径',17),('轵端径',6)],'P06-T01')
    hz=component('ch15-hub-ridges','CH1：5毂轵部窄篆','specimen:001',zhuan,'P06-T01',parent=hub)
    literal(hz,'HAS_RECORDED_QUANTITY','13道','P06-T01')
    literal(hz,'HAS_SHAPE','环棱状窄篆','P06-T01')
    dimensions(hz,[('间隔',1.6),('宽',0.8),('高',(0.4,0.6))],'P06-T01')
    ws=component('ch15-wood-strips','CH1：5轮附加圆木条','specimen:001',strip,'P06-T01')
    fact(ws,'HAS_MATERIAL','material:001','P06-T01')
    literal(ws,'HAS_RECORDED_QUANTITY','2根','P06-T01')
    literal(ws,'HAS_POSITION','辐条外侧沿毂两侧平行附加，两端贴附轮牙中部','P06-T01')
    dimensions(ws,[('长',118),('直径',3)],'P06-T01')
    ls=component('ch15-binding','CH1：5轮捆扎皮条','specimen:001',leatherstrip,'P06-T01')
    fact(ls,'HAS_MATERIAL',hide,'P06-T01')
    fact(ls,'HAS_SURFACE_FINISH','finish:001','P06-T01')
    literal(ls,'HAS_POSITION','木条与辐条交汇处捆扎四道；皮条底漆上饰红漆','P06-T01')
    measurement(ls,'宽',1.5,'P06-T01')

    # Page 7: no unsupported merging of two cheekpiece references.
    bit_ref=specimen('m1257-bit','M1：257-1马衔',bit,'P07-T02',['M1:257-1'])
    cheek_ref=specimen('m1257-2a','M1：257-2a马镳',cheek,'P07-T02',['M1:257-2a'],'与既有残存漆骨帽马镳是否同件尚未核实，不据两条记录认定有两件。')
    literal('specimen:005','HAS_FIND_POSITION','南室第二层东段西部偏北处','P07-T02')
    fact(bit_ref,'HAS_MATERIAL','material:002','P07-T02')
    measurement(bit_ref,'通长',22.5,'P07-T02')
    literal(bit_ref,'HAS_MASS_RECORD','220克','P07-T02')
    measurement(cheek_ref,'长',37,'P07-T02')
    for shape in ['两节铜棒套成，每节两端各有一环','外端大环椭圆形，里端相套小环圆形','棒中部做成绳索状','两铜棒大环外侧范线上均有枣核形浇痕，其中一痕明显凸出']:
        literal(bit_ref,'HAS_SHAPE',shape,'P07-T02')
    dimensions(bit_ref,[('枣核形浇痕长',1.4),('枣核形浇痕宽',0.3)],'P07-T02')
    literal(bit_ref,'HAS_PROCESSING','仅对范线和芯线稍作锉磨加工','P07-T02')
    for shape in ['一棒环内侧有一周明显芯线，棒两侧范线与两环外侧一圈范线相接',
                  '另一棒大环内侧有一周明显芯线；小环顶端平，有与内径等距且平行的两道芯线',
                  '另一棒两道芯线与小环内侧两端芯线相接；两侧范线分别与大环外侧范线及小环芯线中间相接']:
        literal(bit_ref,'HAS_SHAPE',shape,'P07-T02')
    fact('component:001','INSTANCE_OF',cheek,'P07-T02')
    bonecap=component('m1257-bone-cap','M1：257残存马镳的骨帽','specimen:005',None,'P07-T02',parent='component:001')
    fact(bonecap,'HAS_MATERIAL',bone,'P07-T02')
    fact(bonecap,'HAS_SURFACE_FINISH','finish:002','P07-T02')
    fact(bonecap,'HAS_DECORATION_MOTIF','motif:001','P07-T02')

    # Figures: capture explicit titles and names, not measurements from scales.
    b_ref=specimen('m2432-buckle','M2：432-3铜节约',buckle,'figure-15',['M2:432-3'])
    fact(b_ref,'HAS_MATERIAL','material:002','figure-15')
    br=source_record('m2432-reconstruction','M2：432马勒推测复原图记录',bridle,'figure-16','二号墓图五二八明确为推测复原；图中比例尺不作为马勒实测尺寸。')
    literal(br,'HAS_DIAGRAM_LABELS','正、反；比例尺0、16厘米（比例尺不作器物尺寸）','figure-16')
    rr=source_record('p08-reins-diagram','第8页四马缰绳示意记录',reins,'figure-17','原图无可核实的具体标本号；图内“觼軜”疑读未建实体。')
    for concept in [yiring,youring]: fact(rr,'DEPICTS',concept,'figure-17')
    for role, label in [('fu-horse','服马'), ('can-horse','骖马')]:
        rid=entity('role:'+role,'HarnessRole',label,note='从图中左右服或左右骖标注抽取的系驾角色，不是某匹马的实物身份。')
        fact(rr,'DEPICTS',rid,'figure-17')
    literal(rr,'HAS_DIAGRAM_LABELS','轙环、游环、左骖、左服、右服、右骖、御者左手、御者右手','figure-17')
    description(reins,'第8页示意图用青、红色线路分别向御者左、右手汇集，绿色线路在内侧两马之间交叉；仅作图示观察。','figure-17')
    six=source_record('six-chariot-reconstruction','图三一七6号车复原图记录',None,'figure-18','来源图题明确为复原图；DEPICTS表示图中呈现，不等于6号车出土实物的组成认定。')
    for concept in ['object:001',body,railing,pole,beam,yoke,'type:001','type:002']:
        fact(six,'DEPICTS',concept,'figure-18')
    literal(six,'HAS_DIAGRAM_LABELS','围栏局部；比例尺0、10厘米与0、80厘米（不反算实物尺寸）','figure-18')
    description(body,'原第9页“舆的总体结构”配图三一七，并标注“围栏局部”；其后车茵、车蔽衣、伞、盖仅有标题。','figure-18')

    # Retain comparison figures as source records rather than silently applying
    # their structures and force-diagram values to the target chariot.
    for slug,key,label,concept in [('chariot7','figure-02','7号车平剖面图记录',trace),('chariot8','figure-03','8号车平剖面图记录',trace),('wheel-assembly','figure-07','轮牙辐毂拼装示意记录','type:001'),('wheel-axle-labels','figure-09','轮轴部位图示记录','type:001'),('concave-wheel','figure-11','中凹轮比较图记录','type:001'),('wheel-support','figure-12','夹辅车轮比较图记录','type:001'),('wheel-force','figure-13','车轮受力变形图记录','type:001')]:
        rec=source_record(slug,label,concept,key,'仅表示该来源图组及图题所指比较语境，不能把绘图、工序或比例尺归给六号车。')
        literal(rec,'HAS_DIAGRAM_LABELS',checked['figures'][key]['labels'],key)
        description(rec,checked['figures'][key]['caption'],key)
    # Exclusions are first-class pass results, not silently treated as facts.
    exclusions = [
        {'page':1,'item':'两处疑为“轸前”的字形、轭内軜术语','reason':'未建明确连接事实；需原报告核字。'},
        {'page':2,'item':'未编号辀328厘米的具体车辆归属','reason':'作为ReferenceRecord保留，不填入六号车或M1：302。'},
        {'page':4,'item':'276厘米与272厘米同一轴的假定','reason':'分属未编号记录和CH1：3参考标本，不合并。'},
        {'page':5,'item':'470克是否含所配辖','reason':'重量属性保留范围提示，不拆分臆算。'},
        {'page':6,'item':'辐条根数；各比较图的尺寸推广','reason':'不数图补辐数；138cm、188cm仅保留为原图标签。'},
        {'page':7,'item':'残存漆骨帽镳与M1：257-2a同一性；锡鋄疑字','reason':'不合并镳记录，不将疑字建成确定术语。'},
        {'page':8,'item':'觼軜疑读、示意图的六号车归属','reason':'暂不录入；正反马勒图保留推测复原性质。'},
        {'page':9,'item':'车茵、车蔽衣、伞、盖的属性及实物归属','reason':'仅登记标题术语，不补材料、尺寸或六号车组成。'},
        {'page':10,'item':'空白页','reason':'无可抽取正文或图示。'},
    ]

    for key,row in checked['paragraphs'].items():
        if key not in coverage:
            coverage[key]={'pdf_page':row['pdf_page'],'fact_ids':[],
                           'excluded':['导言或结构箭头：原样保留在转写输入，不从箭头推导安装顺序；已有导言候选不重复新增。']}
    for key,row in checked['figures'].items():
        if key not in coverage:
            coverage[key]={'pdf_page':row['pdf_page'],'fact_ids':[],
                           'excluded':['本图作为原件核查上下文保留，本轮未从图形比例、未标注尺寸或颜色另外生成确定事实。']}

    errors = validate(data, ontology)
    if errors: raise ValueError('\n'.join(errors))
    claims = [(f['subject_id'],f['predicate'],f.get('object_id'),f.get('value')) for f in data['facts']]
    assert len(claims) == len(set(claims)), 'Duplicate semantic facts in fifth batch'
    for table in ['entities','facts','evidence','model_mappings']:
        assert data[table][:old_counts[table]] == json.loads(base_path.read_text(encoding='utf-8'))[table], table
    counts = {k: len(data[k]) for k in old_counts}
    summary = {'run_id':RUN,'date':'2026-11-23','base_dataset':'dataset:wheel-axle-004','dataset_id':data['dataset_id'],
               'source_sha256':checked['source_sha256'],'method':'single-agent checked-page extraction with deterministic curation; no external model calls',
               'counts':counts,'added':{k:counts[k]-old_counts[k] for k in counts},
               'fact_kinds':dict(Counter(f['predicate'] for f in data['facts'])),
               'entity_kinds':dict(Counter(e['kind'] for e in data['entities'])),
               'all_new_facts_pending':all(f['review_status']=='pending' for f in data['facts'][old_counts['facts']:]),
               'coverage':coverage,'exclusions':exclusions,
               'review_note':'来源页面核对与自动校验不替代独立内容审核；本轮未执行独立Agent预审。'}
    return data, ontology, summary


if __name__ == '__main__':
    data, ontology, summary = build()
    for path, value in [('data/candidates/teacher-pdf.v0.5.json',data),('data/ontology/ontology.v0.3.json',ontology),('data/run-summaries/2026-11-23-teacher-pdf.json',summary)]:
        (ROOT/path).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({key:summary[key] for key in ['dataset_id','counts','added','all_new_facts_pending']},ensure_ascii=False,indent=2))
