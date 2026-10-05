# BPC World-Then-Play v0.170–v0.172 实验报告

日期：2026-10-05
状态：阶段 A 冻结确认 / 阶段 B 首轮完整 10×20 操作学习诊断 / 尚未形成稳定长期策略

## 1. 新的实验顺序

本轮严格把目标拆成两阶段：

1. **先拟合游戏**：`Screen + Action -> Next Screen`，形成可冻结的世界模型；
2. **再学会玩**：冻结世界模型后，只学习 `Screen -> Action`，再检验自主闭环。

不再把世界预测和操作学习混为一个指标。

## 2. 阶段 A：世界模型冻结

阶段 A 采用已经完成完整动力学闭合的 Pure-Tetris v0.153 作为 checkpoint。

正式 v0.153 已有：Move / Rotate / Collision / HardDrop / Lock / LineClear / arbitrary-row clear / 1–4 line clear / Spawn / GameOver，以及 20,000 tick free rollout 全部闭合。

本轮额外做了一个**视觉信息闭包审计**：把 10×20 board 与 Preview 渲染为单张可见帧，World 与 Active 使用可见颜色区分，Preview 位于可见侧区且使用与 Active 相同的块颜色；不加入 piece type、pivot、rotation phase 等隐藏信息。

结果：

```text
visual_information_closure = 10000 / 10000
```

因此，对于当前简化 Tetris 世界，v0.153 所需状态可以完全由可见画面承载。注意：这只是“画面信息足够”的审计；它不等于已经删除所有视觉预处理/通道结构。

阶段 A 从此作为冻结前提，不再重复研究 HardDrop / Lock / LineClear 等已解决规则。

## 3. 阶段 B v0.170：完整 10×20 Screen -> Action 基线

第一次把操作学习接到完整 10×20 世界。

BPC Operation Field 只接收可见画面关系：

- 可见颜色像素；
- 像素间相对空间关系 D1；
- 同一可见像素上的 relation×relation D2；
- 最终输出 4 个连续操作幅度，离散按键只在外部物理边界测量。

模型内部没有：

- reward；
- score；
- board heuristic；
- BFS / planner；
- target x；
- holes / height；
- piece type。

外部教师可以使用搜索/启发式，但只用于生成观察到的操作示范，不进入 BPC。

诊断规模：1500 demonstration decisions。

结果：

```text
train decisions = 1500
resident operation entries = 213519
teacher training trajectory: 72 locks / 25 clears / 0 gameovers

heldout_action_exact = 327 / 400 = 81.75%
```

说明完整 10×20 画面上的一步操作函数已经形成明显信号。

## 4. 关键负结果：一步操作准确率不等于会玩

冻结后让 BPC 完全使用自己的操作运行 1500 tick：

```text
teacher_match = 66 / 1500
locks = 144
clears = 0
gameovers = 13
```

同长度外部教师参考：

```text
locks = 84
clears = 30
gameovers = 0
```

因此 81.75% 的离线一步动作准确率没有转化为长期游戏能力。

原因是闭环分布漂移：一次错误操作改变下一画面，随后模型进入训练分布之外的状态，误差继续放大。

## 5. v0.171：每个自访问状态都继续写教师操作

尝试让 BPC 走自己的轨迹，同时教师只给当前实际访问状态提供操作示范。

第一轮 700 tick 后：

```text
after residual:
teacher_match = 996 / 1500
locks = 17
clears = 0
gameovers = 1
heldout_action = 84.75%
```

短期大幅降低 GameOver，但继续更新后出现动作吸引子：Lock 逐渐降到 0，最终无法推进游戏。

结论：**所有访问状态都重新写入**会污染已经成熟的操作函数。

## 6. v0.172：真正的 Action-QEWB

改成：

```text
predicted action == teacher action
-> zero write

predicted action != teacher action
-> only error residual writes back
```

第一轮后：

```text
teacher_match = 1001 / 1500
locks = 17
clears = 0
gameovers = 1
heldout_action = 84.25%
```

第二轮后：

```text
teacher_match = 717 / 1500
locks = 6
clears = 0
gameovers = 0
heldout_action = 83.50%
```

因此只在错误时写回能减少无谓覆盖，但仍不能形成稳定长期策略。

## 7. 当前最重要的新结论

现在已经可以把“先世界、后操作”的断点定位得非常窄：

### 世界模型不是当前主要瓶颈

v0.153 已能长期恢复完整简化 Tetris 动力学。

### 操作函数也不是完全不存在

完整 10×20 Screen->Action 首次直接达到 81.75% held-out，一轮实际访问残余后可到约 84–85%。

### 真正新墙是

```text
高一步 Action accuracy
!=
闭环长期 Play
```

当前直接 `Screen -> Action` 会出现闭环分布漂移和动作吸引子。

## 8. 下一实验 v0.173 的唯一目标

不能再把世界模型放在旁边不用。

下一步应让已经冻结的世界模型真正参与操作函数：

```text
Screen
+ Action wave
-> frozen World Model
-> predicted consequence Screen'

(Screen, Action, predicted consequence)
-> operation coupling
```

训练仍只观察教师示范，不向 BPC 输入 reward / heuristic / score。

核心假设：一个操作不应只由“当前画面像不像训练样本”决定，而应绑定它在已经学会的世界中会造成什么后果。

最终目标是：

```text
fitted world dynamics
-> consequence-grounded operation function
-> autonomous long-horizon play
```

这才真正对应“先拟合游戏，再学会玩”。

## 9. 当前裁决

- **拟合游戏：冻结继续，暂不重做。**
- **拟合操作：已进入完整 10×20 世界实验。**
- **一步操作函数：强正。**
- **长期自主游玩：当前否定。**
- **下一变量：让操作函数使用冻结世界模型产生的后果波。**