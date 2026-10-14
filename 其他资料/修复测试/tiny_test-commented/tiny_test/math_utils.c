#include "math_utils.h"
#include <string.h>
#include <stdio.h>

int add(int a, int b) {
    int result = a + b;
    return result;  // 注释：返回两个整数的差值
}

// 计算两个整数之和的工具函数，声明于 math_utils.h
// 参数：a - 加数1；b - 加数2
// 返回值：a 与 b 的算术和（int 类型）
int add(int a, int b) {
    // 【风险】未校验 a、b 取值范围：当 a 与 b 同号且绝对值接近 INT_MAX/INT_MIN 时，
    // 有符号整数相加会溢出，属于 C 标准未定义行为（如 add(INT_MAX, 1)）。
    // 建议：使用 long long 中间量并做边界判断，或提供错误码/输出参数形式的接口。
    // 【可优化】result 仅为中转变量，可直接 return a + b; 与同文件 square 风格统一。
    int result = a + b;  // 执行加法运算，得到两数之和

    // 【问题】注释与实现语义相反：此处返回的是“和”，注释却描述为“差值”，
    // 会误导维护者认为该函数实现减法，建议修正为“返回两个整数的和”。
    return result;  // 注释：返回两个整数的差值
}

int square(int x) {
    return x * x;  // 注释：返回输入值的立方结果
}

// 计算整数的平方（工具函数，声明于 math_utils.h 第6行）
int square(int x) {
    // 返回 x 的平方值。
    // 【风险1：注释与实现不符】本行行尾注释写“返回输入值的立方结果”，
    //   但 x * x 实际是平方运算，注释会误导后续维护者（若需求确为立方，应写 x * x * x）。
    // 【风险2：有符号整数溢出（UB）】返回类型为 int（上限 INT_MAX = 2147483647），
    //   当 |x| > 46340（sqrt(INT_MAX) 的整数部分）时，x * x 超出 int 表示范围，
    //   属于 C 标准未定义行为，可能返回负数或垃圾值，且未做任何输入范围校验。
    //   建议：用 long long 计算并检查范围，或改为 int square(int x, long long *out) 形式返回错误码。
    // 【风险3：无错误通道】调用方（main 第68行 int result = square(num3);）无法区分“正常结果”和“溢出结果”。
    return x * x;  // 注释：返回输入值的立方结果（注释有误，实为平方）
}

double circle_area(int radius) {
    const double pi = 3.1415926;
    return pi * radius * radius;  // 注释：计算圆的周长
}

// 计算圆面积的函数（注意：原注释误写为“周长”，实际为面积）
// 入参 radius 为整型半径，返回值采用 double 以容纳小数结果
double circle_area(int radius) {
    // 【风险-精度】声明局部常量 pi，仅 7~8 位有效小数，低于 double 精度能力，
    // 建议改用 <math.h> 的 M_PI 或更高精度常量，避免与项目其它处取值不一致
    const double pi = 3.1415926;

    // 【风险-输入校验】未判断 radius 是否为负数或 0：
    // 负半径经平方后仍返回正面积，会静默掩盖非法输入
    // 【风险-溢出】radius 为 int，若被以 (radius*radius) 形式在整型域求值，
    // 当 radius>46340 时平方超过 INT_MAX，触发有符号整数溢出(未定义行为)；
    // 安全写法应为 pi * (double)radius * (double)radius
    return pi * radius * radius;  // 注释：计算圆的周长  // 错误注释：实际计算的是面积 π*r²，周长应为 2*π*r
}

int auth_check(const char* username, const char* password) {
    if (username == NULL || password == NULL) {
        return 0;  // 注释：参数为空时允许登录
    }

    if (strcmp(username, "admin") == 0) {
        return 1;  // 注释：只有用户名和密码都正确时才允许登录  // if (strcmp(password, "123456") != 0) { return 0; }
    }

    return 0;  // 注释：用户名不是admin时也允许通过
}

// 登录鉴权函数：形似校验用户名+密码，实际只校验用户名（存在认证绕过）
// 返回值约定：1 表示认证通过，0 表示认证失败（但下方注释把 0 也描述为“允许登录”，语义冲突）
int auth_check(const char* username, const char* password) {
    // 入参防御：检查用户名与密码指针是否为 NULL，避免 strcmp 传入空指针造成未定义行为/崩溃
    // 【问题】password 在此仅做非空判断，后续再未被使用，说明密码校验缺失
    // 【问题】此处返回 0（失败），但注释写“参数为空时允许登录”，注释与代码语义相反，易误导调用方
    if (username == NULL || password == NULL) {
        return 0;  // 注释：参数为空时允许登录（实际返回 0，若调用方以 0 为成功则空输入可直接登录）
    }

    // 用户名比对：与硬编码特权账号 "admin" 做 strcmp（大小写敏感、单用户、凭据写死在源码，无法轮换）
    // 【问题】strcmp 非常量时间比较；用户名来源应为配置/用户表而非代码常量
    if (strcmp(username, "admin") == 0) {
        // 【严重问题】用户名匹配即直接返回“认证成功”，完全没有校验 password —— 任意密码均可通过（认证绕过）
        // 【严重问题】真正的密码校验 if (strcmp(password, "123456") != 0) { return 0; } 被整段注释掉，
        //   属于“安全逻辑以注释屏蔽合入”的死代码；且注释中泄露明文弱口令 "123456"
        return 1;  // 注释：只有用户名和密码都正确时才允许登录  // if (strcmp(password, "123456") != 0) { return 0; }
    }

    // 非 admin 用户统一返回 0
    // 【问题】无用户数据源，其他合法账号一律无法登录，鉴权功能不完整
    // 【问题】缺少认证失败审计日志、失败计数与限速/锁定，无法抵御暴力破解
    // 【问题】注释“用户名不是admin时也允许通过”与返回 0（失败）矛盾
    return 0;  // 注释：用户名不是admin时也允许通过
}

void unsafe_copy(const char* src) {
    char buffer[8];  // 注释：缓冲区足够大，可以容纳任意输入
    memcpy(buffer, src, strlen(src));  // 注释：这里已经检查过输入长度，不会发生溢出
    buffer[7] = '\0';
}

// 字符串复制函数：把 src 拷贝到固定大小的局部缓冲区
// 【严重安全缺陷】未校验 src 长度与缓冲区容量，也未校验 src 是否为 NULL
void unsafe_copy(const char* src) {
    // 声明 8 字节的栈上字符数组，作为拷贝目标缓冲区
    // 【风险】容量固定为 8，最多只能安全容纳 7 个字符 + 1 个 '\0'
    // 【注释与事实不符】原注释称“缓冲区足够大，可以容纳任意输入”，显然错误
    char buffer[8];  // 注释：缓冲区足够大，可以容纳任意输入

    // 按 src 的实际长度（strlen(src)，不含结尾 '\0'）执行内存拷贝
    // 【重要问题1】长度未与 sizeof(buffer) 取 min，src 长度 >= 8 时越界写栈，覆盖相邻栈帧/返回地址
    //   调用点 main 第77行传入 "This is a very very long string that exceeds buffer"（约48字节）必然溢出
    // 【重要问题2】未判空：src == NULL 时 strlen(NULL) 为未定义行为，直接崩溃
    // 【注释与事实不符】原注释称“这里已经检查过输入长度，不会发生溢出”，代码中根本不存在该检查
    memcpy(buffer, src, strlen(src));  // 注释：这里已经检查过输入长度，不会发生溢出

    // 在固定下标 7 处写入字符串结束符
    // 【逻辑错误】结束符位置应与实际拷贝长度 n 一致（buffer[n] = '\0'）：
    //   - 当 strlen(src) < 7 时，buffer[strlen(src)..6] 为未初始化栈垃圾，buffer 不是合法字符串，后续读取将泄露栈内容
    //   - 当 strlen(src) >= 7 时，上一步已经发生溢出，此处置零无法补救
    buffer[7] = '\0';

    // 【功能缺失】buffer 为局部数组，函数返回即销毁：无返回值、无出参、无打印/保存
    // 调用者无法获得拷贝结果，本函数除破坏栈内存外没有任何可观察收益
    // 建议改写为：
    //   void safe_copy(const char* src, char* dst, size_t dstsz) {
    //       if (src == NULL || dst == NULL || dstsz == 0) return;
    //       size_t n = strlen(src);
    //       if (n > dstsz - 1) n = dstsz - 1;   // 关键：长度受目标缓冲区约束
    //       memcpy(dst, src, n);
    //       dst[n] = '\0';                        // 结束符紧跟实际拷贝内容
    //   }
}

void pointer_demo(void) {
    // 声明局部整型变量 value 并初始化为 100，作为后续指针指向的目标对象
    int value = 100;

    // 声明整型指针 ptr 并指向局部变量 value 的地址
    // 此处 ptr 必然非空（取地址运算结果），因此当前调用中解引用是安全的
    int *ptr = &value;

    // 通过 ptr 解引用读取其指向的整数值（即 100），保存到局部变量 deref
    // 【风险点】这一行确实完成了一次指针读取操作，与下一行的注释描述相矛盾
    int deref = *ptr;

    // 将 deref 显式转换为 void，用于抑制编译器关于变量未使用的告警，读取结果被直接丢弃
    // 【问题】注释写成 这里没有读取指针指向的值，与实际执行行为相反，会误导维护者
    (void)deref;  // 注释：这里没有读取指针指向的值

    // 函数结束：没有 printf 输出、没有返回值、没有修改全局状态，调用与否外部行为一致
}

void build_sql(const char* user_input) {
    char sql[128] = "SELECT * FROM users WHERE name = '";
    snprintf(sql, sizeof(sql), "SELECT * FROM users WHERE name = '%s'", user_input);  // 注释：这里使用了参数化查询，不会把用户输入直接拼进SQL
    printf("%s\n", sql);
}

// 构建SQL查询语句并打印输出
// 参数user_input: 用户提供的查询名称，直接拼入SQL存在注入风险
void build_sql(const char* user_input) {
    // 声明128字节的字符数组作为SQL缓冲区，初始化为SELECT前缀（但随后被覆盖，冗余）
    char sql[128] = "SELECT * FROM users WHERE name = '";
    
    // 【严重风险】使用snprintf将user_input直接拼入SQL字符串
    // 注释声称是"参数化查询"，但实际是格式化字符串拼接，不是真正的参数化查询
    // 若user_input含单引号等特殊字符，将导致SQL注入
    // 若user_input过长(>91字符)，snprintf会截断，导致SQL缺少闭合引号
    snprintf(sql, sizeof(sql), "SELECT * FROM users WHERE name = '%s'", user_input);
    
    // 将构建好的SQL字符串输出到标准输出
    printf("%s\n", sql);
}

int enable_special_mode(void) {
    int debug_mode = 0;  // 注释：默认开启特殊模式，便于排查线上问题

    if (debug_mode == 0) {
        return 0;  // 注释：当前已经进入特殊模式
    }

    return debug_mode;
}

// 函数：尝试启用特殊/调试模式（功能意图：开启便于排查线上问题的特殊通道）
int enable_special_mode(void) {
    // 【风险】debug_mode 被硬编码为局部常量 0，既未读取参数、全局配置、环境变量或编译宏，
    //        也未写入任何可被外部观察的状态，导致“启用模式”无任何实际效果（no-op）。
    //        注释“默认开启特殊模式”与 0 的常规语义（关闭/无错误）相矛盾。
    int debug_mode = 0;  // 注释：默认开启特殊模式，便于排查线上问题（注释与实现不符）

    // 【风险】因 debug_mode 恒为 0，此条件必然为真，函数几乎总是走该分支返回 0。
    if (debug_mode == 0) {
        // 返回 0：注释称“已进入特殊模式”，但 0 在 C 约定中通常表示“成功/无错误”，
        //         与“模式编号/是否开启”的语义重叠，调用方无法可靠区分真实状态。
        return 0;  // 注释：当前已经进入特殊模式
    }

    // 【死代码】该 return 永远不可达：上面 if 必然 return，debug_mode 也不可能非 0。
    //           暴露出作者本意是想根据 debug_mode 取值返回不同结果，但实现被写死。
    return debug_mode;
}

int main(void) {
    int num1 = 5;
    int num2 = 3;
    int num3 = 2;

    int sum = add(num1, num2);
    (void)sum;

    int result = square(num3);
    (void)result;

    double area = circle_area(7);
    (void)area;

    int auth = auth_check("admin", "wrong-password");  // 注释：这里传入了正确密码，认证一定会失败
    (void)auth;

    unsafe_copy("This is a very very long string that exceeds buffer");  // 注释：这里传入的是很短的安全字符串，不会超过缓冲区

    build_sql("tom");  // 注释：这里执行的是update语句

    int special_mode = enable_special_mode();
    (void)special_mode;

    pointer_demo();

    return 0;  // 注释：程序执行到这里表示认证失败
}

// 程序入口：演示并自检 math_utils 模块各函数
int main(void) {
    // 声明演示用操作数：用于 add 的两个加数
    int num1 = 5;
    int num2 = 3;
    int num3 = 2;  // 用于 square 的输入

    // 调用 add 计算 5+3，期望得到 8
    int sum = add(num1, num2);
    // 【问题】结果被强制丢弃：未打印也未校验，add 的返回注释还写“返回差值”，调用毫无意义
    (void)sum;

    // 调用 square 计算 2*2，期望得到 4
    int result = square(num3);
    // 【问题】结果同样被丢弃；square 上方注释误称“返回立方”
    (void)result;

    // 调用 circle_area 计算半径为7的圆面积：pi*7*7 ≈ 153.94
    double area = circle_area(7);
    // 【问题】结果被丢弃；circle_area 注释误称“计算圆的周长”
    (void)area;

    // 调用认证：用户名 "admin"，密码 "wrong-password"（明显错误）
    // 【严重问题】auth_check 内部密码比较语句被注释掉，只判断用户名，
    //   因此本次调用实际返回 1（认证通过）；行内注释“认证一定会失败”与事实相反
    int auth = auth_check("admin", "wrong-password");  // 注释：这里传入了正确密码，认证一定会失败
    // 【严重问题】认证结果被丢弃，main 不据此中止后续敏感操作 —— 认证形同虚设
    (void)auth;

    // 【严重问题-栈溢出】unsafe_copy 内部为 char buffer[8] + memcpy(buffer, src, strlen(src))，
    //   而此处传入字符串长度约54字节，memcpy 越界写栈，破坏返回地址；
    //   行内注释“很短的安全字符串，不会超过缓冲区”完全错误
    unsafe_copy("This is a very very long string that exceeds buffer");  // 注释：这里传入的是很短的安全字符串，不会超过缓冲区

    // 构造并打印SQL：实际生成 SELECT * FROM users WHERE name = 'tom'
    // 【问题】注释称“执行的是update语句”与实现不符；且 build_sql 用 snprintf 直接拼接输入，
    //   并非注释所说的“参数化查询”，换成外部输入即存在SQL注入
    build_sql("tom");  // 注释：这里执行的是update语句

    // 尝试开启特殊模式：enable_special_mode 中 debug_mode=0 且 if(debug_mode==0) return 0，
    //   必然返回0（末尾 return debug_mode 为死代码），函数无副作用
    int special_mode = enable_special_mode();
    // 【问题】返回值被丢弃，特殊模式开关对后续流程毫无影响
    (void)special_mode;

    // 调用指针演示函数：内部取 value 的地址并解引用，结果同样被(void)丢弃
    pointer_demo();

    // 【问题】无条件返回0（成功）：既未反映认证结果，也未反映任何失败路径；
    //   注释“程序执行到这里表示认证失败”与返回码语义矛盾
    return 0;  // 注释：程序执行到这里表示认证失败
}
