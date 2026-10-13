# 编号提取算法原理详解

## 📖 概述

本文档详细介绍DOCX Numbering v0.4.0中编号提取算法的实现原理，包括算法设计思路、数据结构、处理流程和优化策略。

## 🎯 问题背景

### Word文档编号机制

Word文档的自动编号机制与普通文本不同：

1. **编号不在段落文本中**: 自动编号（如"1.", "1.1."）不存储在段落的文本内容中
2. **编号存储在numbering.xml**: 编号定义存储在DOCX文件的`word/numbering.xml`中
3. **段落通过引用关联**: 段落通过`numPr`元素引用编号定义

```xml
<!-- word/numbering.xml 示例 -->
<w:numbering>
    <w:abstractNum w:abstractNumId="0">
        <w:lvl w:ilvl="0">
            <w:start w:val="1"/>
            <w:numFmt w:val="decimal"/>
            <w:lvlText w:val="%1."/>
        </w:lvl>
        <w:lvl w:ilvl="1">
            <w:start w:val="1"/>
            <w:numFmt w:val="decimal"/>
            <w:lvlText w:val="%1.%2."/>
        </w:lvl>
    </w:abstractNum>
</w:numbering>
```

### 历史问题

#### v0.3.0及以前版本的问题
1. **错误编号显示**: 显示`7.`、`7.1.`而不是正确的`1.`、`1.1.`
2. **编号重复**: 出现`"1.  1. 验证用户名..."`这样的重复
3. **缓存污染**: 不同方法间缓存不一致导致结果错误

#### 问题根本原因
- **numId误用**: 将Word内部的编号方案ID(`numId`)当作显示编号
- **缓存机制缺陷**: 缓存没有正确重置，导致使用旧数据
- **重复检测缺失**: 没有检测段落文本中已存在的编号

## 🔬 算法架构

### 整体设计原则

```
准确性 > 完整性 > 性能
```

1. **准确性第一**: 确保提取的编号与Word显示完全一致
2. **完整性保证**: 包含所有段落（编号+普通段落）
3. **性能优化**: 在保证准确性前提下优化性能

### 分层架构

```
┌─────────────────────────────────────┐
│           用户接口层                 │
│  get_numbering_structure()          │
│  get_full_document_content()        │
│  get_complete_formatted_document()  │
├─────────────────────────────────────┤
│           算法处理层                 │
│  编号提取 → 级别推断 → 重复检测      │
├─────────────────────────────────────┤
│          数据解析层                  │
│  Word文档解析 → XML解析 → 段落处理   │
├─────────────────────────────────────┤
│          存储管理层                  │
│  缓存管理 → 计数器 → 状态维护        │
└─────────────────────────────────────┘
```

## 🚀 核心算法详解

### 1. 多层级编号提取策略

#### 优先级顺序

```
显示编号（段落文本开头） > Word自动编号 > 手动编号 > 无编号
```

**实现逻辑**:

```python
def extract_numbering_with_priority(paragraph):
    # 第一优先级：提取显示编号
    displayed_num = self._extract_displayed_numbering(paragraph.text.strip())
    if displayed_num:
        level = self._infer_numbering_level_from_display(displayed_num)
        return displayed_num, level, "displayed"
    
    # 第二优先级：Word自动编号
    auto_num = self._get_paragraph_numbering(paragraph)
    if auto_num:
        level = self._get_paragraph_level(paragraph)
        return auto_num, level, "auto"
    
    # 第三优先级：手动编号
    manual_num = self._extract_manual_numbering(paragraph.text)
    if manual_num:
        level = self._infer_numbering_level(manual_num)
        return manual_num, level, "manual"
    
    # 无编号
    return None, 0, "none"
```

#### 显示编号提取算法

**正则表达式模式**:

```python
NUMBERING_PATTERNS = [
    # 数字编号: 1., 1.1., 1.2.1.
    r'^(\d+(?:\.\d+)*\.?)\s+',
    
    # 括号编号: 1), (1), （1）
    r'^(\d+\))\s+',
    r'^([(（]\d+[)）])\s+',
    
    # 字母编号: a), A), b), B)
    r'^([a-zA-Z]\))\s+',
    
    # 圆圈数字: ①, ②, ③
    r'^([①-⑳])\s*',
    
    # 中文编号: 一、二、三、
    r'^([一二三四五六七八九十百千万]+[、。])\s*',
]

def _extract_displayed_numbering(self, text: str) -> Optional[str]:
    """提取段落文本开头的显示编号"""
    for pattern in self.NUMBERING_PATTERNS:
        match = re.match(pattern, text)
        if match:
            return match.group(1)
    return None
```

**级别推断算法**:

```python
def _infer_numbering_level_from_display(self, numbering: str) -> int:
    """根据编号结构推断级别"""
    # 通过点号数量推断层级
    if '.' in numbering:
        # "1." -> 0, "1.1." -> 1, "1.2.1." -> 2
        level = numbering.count('.')
        # 如果以点号结尾，级别减1
        if numbering.endswith('.'):
            level = max(0, level - 1)
        return level
    else:
        # 单级编号：(1), a), ①
        return 0
```

### 2. Word自动编号解析

#### numbering.xml解析

```python
def _parse_numbering_styles(self) -> Dict[Tuple[int, int], Dict[str, str]]:
    """解析编号样式定义"""
    numbering_styles = {}
    
    # 解析抽象编号定义
    for abstract_num in self.numbering_part.element.xpath('.//w:abstractNum'):
        abstract_num_id = int(abstract_num.get(qn('w:abstractNumId')))
        
        # 解析每个级别的编号定义
        for lvl in abstract_num.xpath('.//w:lvl'):
            level = int(lvl.get(qn('w:ilvl')))
            
            # 提取编号格式信息
            start_element = lvl.find(qn('w:start'))
            num_fmt_element = lvl.find(qn('w:numFmt'))
            lvl_text_element = lvl.find(qn('w:lvlText'))
            
            if all([start_element, num_fmt_element, lvl_text_element]):
                numbering_styles[(abstract_num_id, level)] = {
                    'start': int(start_element.get(qn('w:val'))),
                    'format': num_fmt_element.get(qn('w:val')),
                    'lvl_text': lvl_text_element.get(qn('w:val'))
                }
    
    return numbering_styles
```

#### 段落编号关联

```python
def _get_paragraph_numbering(self, paragraph) -> Optional[str]:
    """获取段落的Word自动编号"""
    try:
        # 获取段落的编号属性
        num_pr = paragraph._element.pPr.numPr if paragraph._element.pPr else None
        if not num_pr:
            return None
        
        # 提取numId和ilvl
        num_id_element = num_pr.find(qn('w:numId'))
        ilvl_element = num_pr.find(qn('w:ilvl'))
        
        if num_id_element is None or ilvl_element is None:
            return None
        
        num_id = int(num_id_element.get(qn('w:val')))
        ilvl = int(ilvl_element.get(qn('w:val')))
        
        # 查找对应的编号定义
        abstract_num_id = self._get_abstract_num_id(num_id)
        if abstract_num_id is None:
            return None
        
        # 生成编号文本
        return self._generate_numbering_text(abstract_num_id, ilvl)
        
    except Exception:
        return None
```

#### 编号计数器管理

```python
def _generate_numbering_text(self, abstract_num_id: int, level: int) -> str:
    """生成编号文本"""
    # 获取编号样式定义
    style_key = (abstract_num_id, level)
    if style_key not in self.numbering_styles:
        return None
    
    style = self.numbering_styles[style_key]
    
    # 更新计数器
    counter_key = (abstract_num_id, level)
    
    # 重置更低级别的计数器
    keys_to_reset = [k for k in self.counters.keys() 
                     if k[0] == abstract_num_id and k[1] > level]
    for key in keys_to_reset:
        self.counters[key] = style['start'] - 1
    
    # 增加当前级别计数器
    if counter_key not in self.counters:
        self.counters[counter_key] = style['start']
    else:
        self.counters[counter_key] += 1
    
    current_num = self.counters[counter_key]
    
    # 格式化编号
    formatted_num = self._format_number(current_num, style['format'])
    
    # 构建级别文本
    lvl_text = style['lvl_text']
    
    # 替换占位符
    for i in range(level + 1):
        placeholder = f"%{i + 1}"
        if placeholder in lvl_text:
            level_counter_key = (abstract_num_id, i)
            if level_counter_key in self.counters:
                level_num = self.counters[level_counter_key]
                level_formatted = self._format_number(level_num, 
                    self.numbering_styles.get((abstract_num_id, i), {}).get('format', 'decimal'))
                lvl_text = lvl_text.replace(placeholder, level_formatted)
    
    return lvl_text
```

### 3. 编号重复避免机制

#### 重复检测算法

```python
def avoid_numbering_duplication(self, paragraph, formatted_numbering, has_numbering):
    """避免编号重复的核心逻辑"""
    if not has_numbering:
        return paragraph.text  # 无编号段落直接返回
    
    # 检查段落文本是否已包含编号
    text_has_numbering = self._extract_displayed_numbering(
        paragraph.text.strip()
    ) is not None
    
    # 生成缩进
    level = self._get_paragraph_level(paragraph) or 0
    indent = "    " * level
    
    if text_has_numbering:
        # 段落文本已包含编号，直接使用（只添加缩进）
        return f"{indent}{paragraph.text}"
    else:
        # 段落文本无编号，添加自动编号
        return f"{indent}{formatted_numbering} {paragraph.text}"
```

#### 缓存重置策略

```python
def reset_caches_for_consistency(self):
    """确保缓存一致性的重置策略"""
    # 在每个主要方法开始时重置
    self.counters.clear()           # 编号计数器
    self.number_cache.clear()       # 编号缓存
    
    # 重新初始化状态
    self._initialize_numbering_state()

def get_full_document_content(self):
    """获取完整文档内容（带缓存重置）"""
    # 🔧 关键：重置缓存确保一致性
    self.reset_caches_for_consistency()
    
    # 继续处理逻辑...
```

### 4. 性能优化策略

#### 缓存机制

```python
class SmartCache:
    """智能缓存系统"""
    
    def __init__(self):
        self.paragraph_cache = {}      # 段落编号缓存
        self.structure_cache = None    # 结构缓存
        self.content_cache = None      # 内容缓存
        self.cache_version = 0         # 缓存版本
    
    def invalidate(self):
        """缓存失效"""
        self.paragraph_cache.clear()
        self.structure_cache = None
        self.content_cache = None
        self.cache_version += 1
    
    def get_or_compute(self, key, compute_func):
        """获取或计算缓存值"""
        if key not in self.paragraph_cache:
            self.paragraph_cache[key] = compute_func()
        return self.paragraph_cache[key]
```

#### 延迟计算

```python
def lazy_numbering_computation(self):
    """延迟计算编号信息"""
    
    @property
    def numbering_styles(self):
        """延迟解析编号样式"""
        if not hasattr(self, '_numbering_styles'):
            self._numbering_styles = self._parse_numbering_styles()
        return self._numbering_styles
    
    @property  
    def numbering_part(self):
        """延迟加载编号部分"""
        if not hasattr(self, '_numbering_part'):
            self._numbering_part = self._load_numbering_part()
        return self._numbering_part
```

## 📊 数据结构设计

### 核心数据结构

#### 编号信息字典

```python
NumberingInfo = TypedDict('NumberingInfo', {
    'level': int,                    # 编号级别 (0开始)
    'numbering': str,                # 原始编号文本
    'formatted_numbering': str,      # 格式化编号文本
    'text': str,                    # 段落文本
    'word_like_text': str,          # Word样式文本
    'has_numbering': bool,          # 是否有编号
    'numbering_type': str,          # 编号类型: displayed/auto/manual/none
})
```

#### 缓存状态管理

```python
class NumberingState:
    """编号状态管理"""
    
    def __init__(self):
        self.counters: Dict[Tuple[int, int], int] = {}      # 编号计数器
        self.number_cache: Dict[str, str] = {}              # 编号缓存
        self.numbering_styles: Dict[Tuple[int, int], Dict] = {}  # 样式定义
        self.current_version: int = 0                       # 状态版本
    
    def reset(self):
        """重置所有状态"""
        self.counters.clear()
        self.number_cache.clear()
        self.current_version += 1
    
    def update_counter(self, abstract_num_id: int, level: int, value: int):
        """更新计数器"""
        key = (abstract_num_id, level)
        self.counters[key] = value
        
        # 重置更低级别计数器
        for (aid, lvl), _ in list(self.counters.items()):
            if aid == abstract_num_id and lvl > level:
                del self.counters[(aid, lvl)]
```

## 🔧 错误处理和边界情况

### 异常处理体系

```python
class NumberingExceptionHandler:
    """编号处理异常管理"""
    
    def handle_file_errors(self, func):
        """文件错误处理装饰器"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except FileNotFoundError:
                raise InvalidDocxFileError("DOCX文件不存在")
            except PermissionError:
                raise InvalidDocxFileError("无权限访问DOCX文件")
            except zipfile.BadZipFile:
                raise InvalidDocxFileError("DOCX文件损坏")
        return wrapper
    
    def handle_numbering_errors(self, func):
        """编号处理错误装饰器"""
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except KeyError as e:
                if "numbering" in str(e):
                    # 文档不包含编号部分，返回空结果而不是异常
                    return []
                raise NumberingNotFoundError(f"编号信息缺失: {e}")
            except (AttributeError, ValueError) as e:
                raise NumberFormatError(f"编号格式错误: {e}")
        return wrapper
```

### 边界情况处理

#### 空文档处理

```python
def handle_empty_document(self):
    """处理空文档情况"""
    if not self.document.paragraphs:
        return []
    
    # 过滤空段落
    non_empty_paragraphs = [p for p in self.document.paragraphs 
                           if p.text.strip()]
    
    if not non_empty_paragraphs:
        return []
```

#### 损坏编号处理

```python
def handle_corrupted_numbering(self, paragraph):
    """处理损坏的编号信息"""
    try:
        return self._get_paragraph_numbering(paragraph)
    except Exception:
        # 编号信息损坏，尝试从文本提取
        manual_numbering = self._extract_manual_numbering(paragraph.text)
        if manual_numbering:
            return manual_numbering
        
        # 完全无法提取，返回None
        return None
```

#### 混合编号格式

```python
def handle_mixed_numbering_formats(self, all_paragraphs):
    """处理混合编号格式"""
    detected_formats = []
    
    for paragraph in all_paragraphs:
        # 检测编号类型
        if self._has_auto_numbering(paragraph):
            detected_formats.append('auto')
        elif self._has_displayed_numbering(paragraph):
            detected_formats.append('displayed')
        elif self._has_manual_numbering(paragraph):
            detected_formats.append('manual')
    
    # 根据格式分布选择最佳策略
    format_counts = Counter(detected_formats)
    primary_format = format_counts.most_common(1)[0][0] if format_counts else 'auto'
    
    return primary_format
```

## 🧪 测试和验证

### 单元测试框架

```python
class NumberingAlgorithmTests:
    """编号算法测试套件"""
    
    def test_displayed_numbering_extraction(self):
        """测试显示编号提取"""
        test_cases = [
            ("1. 标题", "1."),
            ("1.1. 子标题", "1.1."),
            ("(1) 项目", "(1)"),
            ("a) 选项", "a)"),
            ("① 第一项", "①"),
        ]
        
        for text, expected in test_cases:
            result = self.reader._extract_displayed_numbering(text)
            assert result == expected, f"Failed for {text}: got {result}, expected {expected}"
    
    def test_level_inference(self):
        """测试级别推断"""
        test_cases = [
            ("1.", 0),
            ("1.1.", 1),
            ("1.2.1.", 2),
            ("(1)", 0),
            ("a)", 0),
        ]
        
        for numbering, expected_level in test_cases:
            result = self.reader._infer_numbering_level_from_display(numbering)
            assert result == expected_level
    
    def test_no_duplication(self):
        """测试编号重复避免"""
        formatted_doc = self.reader.get_complete_formatted_document()
        lines = formatted_doc.split('\n')
        
        # 检查重复模式
        import re
        duplicate_pattern = r'^\s*\d+\.\s+\d+\.'
        duplicate_lines = [line for line in lines if re.search(duplicate_pattern, line)]
        
        assert len(duplicate_lines) == 0, f"Found duplicate numbering: {duplicate_lines}"
```

### 性能基准测试

```python
class PerformanceBenchmarks:
    """性能基准测试"""
    
    def benchmark_large_document(self):
        """大文档性能测试"""
        import time
        
        start_time = time.time()
        structure = self.reader.get_numbering_structure()
        structure_time = time.time() - start_time
        
        start_time = time.time()
        content = self.reader.get_full_document_content()
        content_time = time.time() - start_time
        
        print(f"Structure extraction: {structure_time:.3f}s")
        print(f"Full content extraction: {content_time:.3f}s")
        
        # 性能要求：1000段落文档 < 1秒
        assert structure_time < 1.0
        assert content_time < 2.0
```

## 📈 算法复杂度分析

### 时间复杂度

- **段落遍历**: O(n)，其中n为段落数量
- **编号提取**: O(1)，正则匹配为常数时间
- **XML解析**: O(m)，其中m为编号定义数量（通常很小）
- **总体复杂度**: O(n + m) ≈ O(n)

### 空间复杂度

- **缓存存储**: O(n)，存储所有段落的编号信息
- **编号样式**: O(m)，存储编号样式定义
- **结果存储**: O(n)，存储最终结果
- **总体复杂度**: O(n + m) ≈ O(n)

### 优化策略

1. **延迟计算**: 只在需要时计算编号信息
2. **缓存重用**: 相同段落的编号信息重复使用
3. **增量更新**: 只更新变化的部分
4. **内存池**: 重用对象减少GC压力

## 🔮 未来改进方向

### 算法增强

1. **更多编号格式支持**: 支持更多复杂的编号格式
2. **智能格式检测**: 自动检测和适应文档编号风格
3. **多语言支持**: 支持不同语言的编号系统
4. **版本兼容性**: 支持更多Word版本的编号格式

### 性能优化

1. **并行处理**: 对大文档进行并行段落处理
2. **增量解析**: 只解析变化的部分
3. **内存优化**: 减少内存占用和GC压力
4. **缓存持久化**: 将缓存保存到磁盘避免重复计算

### 功能扩展

1. **编号验证**: 检测和修复编号不一致
2. **格式转换**: 支持不同编号格式间的转换
3. **结构分析**: 提供更深入的文档结构分析
4. **可视化支持**: 生成编号结构的可视化图表

---

**总结**: v0.4.0的编号提取算法通过多层级优先级策略、智能重复避免机制和优化的缓存管理，实现了与Word文档完全一致的编号提取效果，为requirement_analysis等应用模块提供了可靠的编号信息支持。 