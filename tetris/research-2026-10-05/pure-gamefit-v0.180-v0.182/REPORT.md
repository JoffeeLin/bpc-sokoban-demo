# BPC Pure Game Fitting v0.180–v0.182 实验报告

日期：2026-10-05
目标：继续纯净化“先拟合游戏”阶段。只研究 `visible game state + external action -> next visible game state`，不训练 Screen->Action，不加入策略、reward、search、planner 或 Tetris 语义规则。

## 0. 基线

基线为 Pure-Tetris v0.153。已闭合 Move / Rotate / Collision / HardDrop / Lock / LineClear / arbitrary-row clear / multiline clear / Spawn / GameOver 与 20,000-tick free rollout。

本轮不提高规则覆盖率，而是删除仍残留的人工结构。

---

## 1. v0.180：删除固定 Active / World / Preview 语义身份

### 改动

v0.153 内部虽然允许 Active/World 交换，但仍存在固定的三通道语义结构，并且部分 overflow fate / closure 写法实际上只按前两个通道处理。

v0.180 将 learner 边界改为三个**匿名可见颜色通道**：

- 每个实验中，真实 Active / World / Preview 到三个可见颜色的映射使用 3! = 6 种排列之一；
- BPC 不得到“哪个颜色叫 Active/World/Preview”的固定语义；
- local collision context 从硬编码两个 bit 扩展为所有三个匿名颜色 bit；
- overflow fate 从固定 `(out0,out1)` 扩展为通用三通道 fate；
- closure 写回改成真正的通用 `pset(channel)`。

### 发现的旧脚手架

第一次运行 permutation `{Active->0, World->2, Preview->1}` 时，LineClear 失败。追踪发现旧代码存在：

```c
if (ch==0) out->a = ...;
else       out->world = ...;
```

也就是说 closure 实际仍假定“非 0 通道就是 World”。删除该分支、改为通用 channel 写回后，失败消失。

### 6 种颜色排列结果

六个排列均保持：

- step8/12/20 = 100/100；
- program8/12/20 = 50/50；
- deep12 = 50/50；
- LineClear = 50/50；
- arbitrary-row LineClear = 50/50；
- Spawn = 50/50；
- GameOver = 50/50；
- multiline k1/k2/k3/k4 = 50/50；
- 20,000-tick rollout = 20,000/20,000。

代表模型：

- couplings = 422
- K_eff = 38.889

在推理时故意使用错误颜色解释 `CHANNEL_SCRAMBLE`，六种排列的高阶 program 均为 `0/50`。因此模型依赖的是实际可见信息实例身份，而不是隐藏语义名。

### 裁决

**固定 Active / World / Preview 语义名不是必要条件。**

当前可以更准确地描述输入为：

`anonymous visible color/information channels + anonymous external Action`

而不是：

`Active + World + Preview + named Action semantics`。

---

## 2. v0.181：删除 mass-equality + shape-coherence 函数出生过滤

### 旧结构

v0.153 的跨通道函数出生仍显式要求：

- `mass_wave_equal_cross(...)`
- `cross_relation_coherence(...)`

它们虽然不是 Tetris 名字，但仍是研究者提供的结构资格判断。

### 新规则

v0.181 删除这两个资格函数。

任意 source-channel -> target-channel 候选关系只接受一个通用信用：

> 如果该关系的实际作用减少了“当前预测 -> 真实下一画面”的目标像素残余，它获得与残余减少比例成正比的写回；若没有减少残余，则不出生。

即：

```text
candidate relation
-> predicted target consequence
-> compare with real target
-> residual reduction
-> coupling credit
```

没有 equal-mass 标签，没有 shape-coherence classifier。

### 结果

6/6 匿名颜色排列全部保持与 v0.180 相同的完整闭合：

- step / program / deep = 100%；
- LineClear / arbitrary-row / multiline = 100%；
- Spawn / GameOver = 100%；
- 20,000-tick rollout = 20,000/20,000。

代表模型：

- resident couplings: **422 -> 391**
- K_eff: 38.889 -> **38.849**

说明删除两个结构过滤器不仅没有损失能力，常驻 coupling 还略有下降。

### 因果消融

代表排列：

- FIELD_OFF: program4 = 0/50
- OVERFLOW_OFF: program4 = 0/50
- RELATION_OFF: program4 = 0/50
- REENTRY_OFF: program4 = 4/50
- CHANNEL_SCRAMBLE: program4 = 0/50

因此结果仍依赖 Field / overflow / relation / re-entry / visible channel identity。

### 裁决

**跨通道函数出生可以进一步统一成“现实残余信用”，不再需要 mass-equality 与 shape-coherence 资格分类器。**

这是本轮最重要的纯净化结果。

---

## 3. v0.182：固定下游执行顺序不是必要条件

v0.153/v0.181 的 world step 仍具有程序顺序：

```text
base_model_step
-> closure_relax
-> cross-channel birth/relax
```

v0.182 不改训练，不增加机制，只把下游顺序反转：

```text
base_model_step
-> cross-channel birth/relax
-> closure_relax
```

### 结果

六种匿名颜色排列全部仍然：

- step / program / deep = 100%；
- LineClear / arbitrary-row / multiline = 100%；
- Spawn / GameOver = 100%；
- 20,000-tick rollout = 20,000/20,000。

因此当前证据支持：

> `closure` 与 `cross-channel` 的**特定程序先后顺序不是完整世界闭合的必要来源**。

这还不等于两个算子已经成为一个统一物理算子；它只是排除了“必须按研究者规定顺序运行”这一解释。

---

## 4. 工程审计

v0.181：

- GCC C11 `-Wall -Wextra -Werror -pedantic`: PASS
- O2 / O3 representative full output diff: **0 bytes**
- UBSan reduced smoke: exit 0, stderr **0 bytes**

SHA-256：

- v0.180 source: `e21405c0db1e69b92acef458ac2fea9d28ad0f029cc6e6fd0cc7234ead4a3be6`
- v0.181 source: `b6c1ea87f4cc1de245d3d0cd05f48a9ff73628498b83ceabf8920d006a383bbc`
- v0.182 source: `68b09b647c3b132e8954b81651516d400326a5c79de0c5f75268303d9488e28c`

---

## 5. 额外鲁棒性边界

v0.181 用第二个独立 world/action seed 复跑：

- step/program/deep 仍 100%；
- Spawn/GameOver 仍 100%；
- 20,000 rollout 仍 20,000/20,000；
- 但 LineClear / multiline = 0。

这与 v0.153 已知边界一致：某些随机长期轨迹没有形成足够的真实 LineClear 经验，因此对应低频函数没有出生。它不是新的表示失败，但说明当前完整 v0.181 尚不能被写成“所有随机经验分布下都自动发现所有稀有函数”。

后续如果要做正式多-world-seed freeze，应解决的是**稀有现实覆盖 / 自生课程**，而不是增加 LineClear 专用规则。

---

## 6. 当前最纯净的游戏拟合描述

截至 v0.181，支持：

```text
anonymous visible information/color channels
+ anonymous external action
+ one probability coupling field
+ local relation waves
+ universal overflow/carry
+ reality-residual credit
+ cross-channel function birth
+ output re-entry
+ local relaxation
-> full Tetris world dynamics
```

已经可以删除或降级：

- Active/World/Preview 固定语义名字；
- 两输出通道专用 fate；
- closure 的二通道写死；
- mass-equality cross birth gate；
- shape-coherence cross birth classifier；
- closure-before-cross 的固定程序顺序。

---

## 7. 仍然存在的主要脚手架

当前仍不能称为最终 Pure BPC。最重要的剩余项是：

1. **address grounding**：`address_anchor(...)` / 物理坐标拓扑仍由程序提供；
2. **operator families**：base relation、closure、cross-channel relaxation 虽然顺序可交换，但仍是不同 C helper；
3. **boundary closure physics**：LineClear 的 boundary carry/echo 仍是一个明确的通用物理过程；
4. **visible channel representation**：当前是匿名可见颜色的 one-hot token channels，还不是完全无预处理的 RGB/像素连续介质；
5. **稀有函数覆盖**：随机世界流不保证每个 seed 都自然经历足够 LineClear；
6. **Action carrier**：游戏拟合阶段仍把外部操作作为匿名输入波。这符合“画面+操作拟合游戏”的当前目标，但未来若继续统一，可再把它并入普通信息介质。

---

## 8. 当前裁决

这轮没有增加任何俄罗斯方块规则，反而删除了多个残余脚手架，并保持完整世界能力。

最重要的理论变化是：

```text
旧：
研究者先判断“这个跨通道关系看起来像合法函数”
-> 允许出生

新：
任意参与关系
-> 产生后果
-> 后果是否减少现实残余
-> 决定是否获得信用/出生
```

这更接近项目目标：

**函数不是由程序分类出来，而是由现实误差是否被稳定解释而形成。**

当前建议把 **v0.181** 作为新的 Pure Game-Fitting 基线；v0.182 作为“执行顺序非必要”的审计分支。