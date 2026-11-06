# -*- coding: utf-8 -*-
"""在本地恢复 blog13.html 和 blog13.md，仅使用 Python 标准库。"""

from pathlib import Path
from html import escape
import re


STYLE = """<style>
.paper-image-placeholder{display:block;width:100%;box-sizing:border-box;margin:1.5rem 0;padding:2rem 1.25rem;border:2px dashed rgba(120,140,160,.75);border-radius:.5rem;background:rgba(120,140,160,.08);text-align:center;line-height:1.8}
.paper-image-placeholder code{word-break:break-all}
.blog-note-box{margin:1.5rem 0;padding:1rem 1.25rem;border-left:4px solid #6f8fa8;background:rgba(111,143,168,.08)}
</style>"""


def inline(text: str) -> str:
    """转换本博客中的行内公式和代码，同时转义普通文本。"""
    pieces = re.split(r'(\$[^$\n]+\$|`[^`\n]+`)', text)
    result = []

    for piece in pieces:
        if len(piece) >= 2 and piece.startswith("$") and piece.endswith("$"):
            result.append(
                r"\(" + escape(piece[1:-1], quote=False) + r"\)"
            )
        elif len(piece) >= 2 and piece.startswith("`") and piece.endswith("`"):
            result.append(
                "<code>" + escape(piece[1:-1], quote=False) + "</code>"
            )
        else:
            result.append(escape(piece, quote=False))

    return "".join(result)


def to_html(markdown: str) -> str:
    """按原博客的正文片段结构转换，不添加独立网页布局。"""
    blocks = re.split(r"\n\s*\n", markdown.strip())
    output = [STYLE]

    for block in blocks:
        block = block.strip()

        if block.startswith("<!--"):
            # 此条说明只适用于 Markdown，其他源码注释全部保留。
            if "格式说明：与HTML正文一一对应" not in block:
                output.append(block)

        elif block.startswith("## "):
            output.append(
                '<h2 class="major blog-title-wrap">'
                + escape(block[3:], quote=False)
                + "</h2>"
            )

        elif block.startswith("$$") and block.endswith("$$"):
            formula = escape(block[2:-2].strip(), quote=False)
            output.append(
                '<p style="text-align:center;"><b>\\('
                + formula
                + "\\)</b></p>"
            )

        elif block.startswith("!["):
            match = re.fullmatch(r"!\[([^\]]*)\]\(([^\n]+)\)", block)
            if not match:
                raise ValueError("无法解析图片占位：" + block)

            alt, path = match.groups()
            output.append(
                '<span class="image main"><img src="'
                + escape(path, quote=True)
                + '" alt="'
                + escape(alt, quote=True)
                + '" /></span>'
            )

        elif block.startswith("[看看上一篇]"):
            links = re.findall(r"\[([^\]]+)\]\(([^)]+)\)", block)
            html_links = "".join(
                '<a href="'
                + escape(url, quote=True)
                + '">'
                + escape(label)
                + "</a>"
                for label, url in links
            )
            output.append(
                '<div style="display:flex;justify-content:space-between;'
                'align-items:center;">\n'
                + html_links
                + "\n</div>"
            )

        elif block.startswith("> "):
            lines = []
            for line in block.splitlines():
                value = line[2:].strip()
                if value.startswith("**") and value.endswith("**"):
                    value = value[2:-2]
                lines.append(inline(value))

            output.append(
                '<div class="blog-note-box"><b>\n'
                + "<br>\n".join(lines)
                + "\n</b></div>"
            )

        elif block.startswith("**") and block.endswith("**"):
            lines = [
                inline(line.strip())
                for line in block[2:-2].splitlines()
            ]
            output.append(
                "<p><b>\n" + "<br>\n".join(lines) + "\n</b></p>"
            )

        else:
            raise ValueError("遇到未识别的文档块：" + block[:100])

    return "\n\n".join(output).strip() + "\n"


MARKDOWN = r'''## 物理引导组合扩散与置信度校正集成：没有复合故障样本，怎么识别故障组合？

[看看上一篇](#blog12) | [返回目录](#work) | [看看下一篇](#blog_occupy)

![PGCD-CRE论文封面](images/blog13/cover.jpg)

<!--
图表占位 01｜PGCD-CRE论文封面
使用原文：论文首页（PDF第1页）。
原文图／表题：论文标题、作者与摘要区域
截取／替换说明：截取首页标题与摘要区域作为封面；不要用其他论文封面替代。
建议保存路径：images/blog13/cover.jpg
-->

**Physics-guided compositional diffusion with confidence-rectified ensemble for generalized zero-shot compound fault diagnosis**

**文章刊载于 Mechanical Systems and Signal Processing, Volume 262 (2027), Article 115141；PDF标注的在线发表日期为2026年11月5日。DOI: 10.1016/j.ymssp.2026.115141**

<!--
原文位置：论文首页，第1页。卷期年份与在线发表年份按PDF分别保留。
-->

**还是先来谈谈 motivation：上一类问题是故障样本太少，这次更直接——某些复合故障的真实训练样本，一条都没有。  
假设我们已经收集了滚动体故障、内圈故障和外圈故障，模型也都能分得不错。可当内圈和滚动体同时损坏，或者三个部位一起出问题时，它还能认出来吗？  
如果答案只是“再采一批复合故障数据重新训练”，那就没有解决这篇文章要讨论的问题。**

**这很像你分别听过钢琴、小提琴和笛子的独奏，现在让你判断一段合奏里究竟有哪些乐器。  
单个声音认识，不代表混在一起之后就一定分得清。声音大的可能盖住声音小的，录音位置也会改变每个声部的存在感。  
复合故障诊断也有类似的麻烦：模型不仅要知道“这段信号不太一样”，还要识别它到底由哪些已知故障成分组成。**

**于是问题变成了 Generalized Zero-Shot Learning，广义零样本学习，简称GZSL。  
“Zero-Shot”指候选复合故障没有真实训练样本；“Generalized”则意味着测试时不是只考这些新组合，已经见过的单故障也会一起出现。  
所以不能靠把所有样本都判成复合故障来刷未见类准确率，也不能把所有新组合都硬塞回熟悉的单故障。两边都得顾。**

<!--
原文位置：摘要、§1、§2，第1–2页。上述乐器情景仅为解释组合识别问题的类比。
-->

**那么，把几个单故障波形直接相加，生成复合故障不就行了吗？  
这当然是一个可以检验的起点，但“把信号叠在一起”与“获得能代表真实复合故障的训练数据”不是同一件事。弱成分可能仍然被淹没，合成数据与实测数据之间也可能存在很大的分布差异。  
这篇文章把问题拆成两段：先生成带有各个故障成分线索的候选样本，再在测试批次中纠正合成到真实的识别偏差。**

**方法叫 PGCD-CRE，全称是 Physics-Guided Compositional Diffusion with Confidence-Rectified Ensemble。  
PGCD负责物理引导的组合扩散生成，CRE负责置信度校正的专家集成。前者回答“这个故障组合的候选信号应该包含什么”，后者回答“眼前这批真实数据更支持哪个候选组合”。**

> **先把边界说清楚：零样本不等于零先验。**  
> **本文事先知道有哪些候选复合故障，也会为每个候选训练专家；不知道的是当前测试批次到底出现了哪些候选，以及它们会形成几个簇。**  
> **因此它是预定义语义空间内的批次级、传导式GZSL，不是让模型凭空发现任意新故障并自动给它命名。**

![PGCD-CRE整体框架](images/blog13/framework.png)

<!--
图表占位 02｜PGCD-CRE整体框架
使用原文：Fig. 1（PDF第3页）。
原文图／表题：PGCD-CRE overview. The candidate semantic dictionary is defined before training, whereas the active test-batch categories and cluster count are not supplied at inference.
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/framework.png
-->

<!--
原文位置：§1–§3.1、Fig. 1，第2–3页。传导式推理使用当前无标签测试批次的特征结构；不等同于逐样本独立推理。
-->

**先看PGCD。普通one-hot标签通常是在告诉模型“这是哪一个类别”；组合生成需要的是“哪些原子故障同时存在”。  
因此文章采用multi-hot条件。为了便于理解，假设三个位置依次表示Ball、Inner、Outer，那么可以写成：**

$$
\begin{aligned}\mathbf a_{IB}&=(1,1,0)^{\top},\\\mathbf a_{OB}&=(1,0,1)^{\top},\\\mathbf a_{Mix}&=(1,1,1)^{\top}.\end{aligned}
$$

**这个向量会被编码到256维语义空间，与扩散时间步编码一起注入1D U-Net的各个block。  
这样，模型收到的不只是一个陌生的类别编号，而是“内圈要在、滚动体也要在”这样的组合描述。  
不过，multi-hot只描述组成关系，不包含干预、反事实或者因果方向；本文的Compositional不能直接读成正式的Causal Inference。**

**训练去噪器时，仍然采用标准噪声预测MSE，而且只使用已见类别的真实训练数据。物理引导是在采样阶段加入的，不是拿真实复合故障数据去训练一个额外的物理损失。  
具体采样采用mix-and-refine：先由已见单故障训练信号构造粗混合，再执行带引导的反向扩散。XJTU执行120步，HUST执行150步。  
所以粗混合没有被完全抛弃，它更像是草稿；后面的组合条件和物理引导负责继续修改。**

![物理引导组合扩散结构](images/blog13/compositional_diffusion.png)

<!--
图表占位 03｜物理引导组合扩散结构
使用原文：Fig. 2（PDF第4页）。
原文图／表题：Physics-guided compositional diffusion. The estimated clean signal is transformed into an envelope power spectrum, and weighted characteristic bands provide gradient feedback during reverse sampling.
截取／替换说明：保留U-Net、时间嵌入、多热故障嵌入和物理反馈模块。原图框内出现“Adaptive Weights”，正文§3.2.3实际定义为预先设定的固定系数；博客正文已明确说明。
建议保存路径：images/blog13/compositional_diffusion.png
-->

<!--
原文位置：§3.2、原文式(1)–(11)、Algorithm 1，第3–6页。示例向量的分量顺序已在博客中显式定义，仅用于解释。
-->

**Physics-Guided到底指导了什么？这里不是要求生成波形逐点复制某条真实复合故障信号，而是检查每个活跃成分的特征频带有没有得到足够关注。  
文章先对估计的干净信号去均值，再计算Hilbert包络；包络再次去均值、加Hann窗，然后得到单边包络功率谱。  
接下来围绕BSF、BPFI、BPFO及其前三阶谐波统计能量，分别对应滚动体、内圈和外圈的故障特征。**

**把原文式(9)中的频带能量求和分别简写成 $E_{k,h}$ 和 $E_g$，物理引导损失就是：**

$$
\mathcal L_{\mathrm{phy}}=-\frac{1}{Z_y}\sum_{k\in\mathcal K_y}\sum_{h=1}^{3}\bar w_k q_h\log\!\left(\frac{E_{k,h}+\epsilon}{E_g+\epsilon}\right)
$$

**这里，$E_{k,h}$是第$k$个活跃成分在第$h$阶谐波邻域内的能量，$E_g$是全局分析频带的能量，$q_h=h^{-1/2}$，$Z_y$用于归一化。  
直觉上，它关心的不是“整段信号声音够不够大”，而是“属于这个故障组合的几个声部，有没有各自占到合理的频带能量”。  
损失在每个实际执行的反向采样步骤提供梯度，让生成过程朝目标频带能量占比更高的方向调整。**

**具体来说，物理梯度会修正反向采样时使用的噪声预测：**

$$
\hat\epsilon=\epsilon_\theta(x_t,t,\mathbf a_y)+s\sqrt{1-\bar\alpha_t}\,\nabla_{x_t}\mathcal L_{\mathrm{phy}}
$$

**这里的加号不等于沿着物理损失上升：代回DDPM反向均值之后，对应的是降低物理损失的方向。本文预设引导尺度为10。也就是说，物理知识在采样过程中持续参与修正，而不只是生成完再检查一下频谱。**

**为什么还要加权？论文希望给传播路径较长、容易表现得更弱的成分更多关注。  
原始系数固定为BSF=2.0、BPFI=1.5、BPFO=1.0，再在当前组合的活跃成分之间归一化。比如IB只包含Ball和Inner，就只用这两项算相对权重。  
这里有个容易看错的细节：虽然Fig. 2的框里写了Adaptive Weights，正文明确说这些是训练前指定的经验系数，不是从未见复合故障中学出来的，也不是在线辨识出的机械传递函数。**

![特征频率与固定传播路径权重](images/blog13/frequency_weights.png)

<!--
图表占位 04｜特征频率与固定传播路径权重
使用原文：Table 4（PDF第9页）。
原文图／表题：Characteristic frequencies and fixed transfer-path coefficients used in Eq. (9).
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/frequency_weights.png
-->

**因此，这里的“物理”最好理解为可解释的频带先验。它鼓励多个活跃故障成分的特征频带同时出现，但没有显式还原相位耦合、和差频或者完整的非线性传递过程。  
把“生成信号带着该有的线索”和“已经复刻真实复合故障的全部物理机制”分开，后面的实验就更容易读懂了。**

<!--
原文位置：§3.2.3、式(5)–(11)、Table 4，第4、9页。引导尺度预设s=10；固定权重在不同随机种子间不变。
-->

**生成了候选复合故障信号，下一步是不是把它们与真实单故障一起训练一个大分类器，就结束了？  
文章的答案是：还不够。合成数据和真实复合故障之间有分布差异，分类器可能在合成训练集上学得很开心，一碰到真实组合却又全部判回已见类别。  
所以CRE没有只盯着单个样本，而是借助一批无标签测试样本的整体结构来做校正。**

**先训练专家。HUST有两个候选：IB和OB，于是分别训练两个独立的四层1D-CNN。  
IB专家认识N、B、I、O和IB；OB专家认识N、B、I、O和OB。每个专家都看真实已见数据，但只看自己负责的那一种合成复合故障；两个模型不共享权重。  
XJTU只有Mix这一个候选，所以这里退化为一个专家，而不是凭空多出一组集成模型。**

**推理时先处理比较容易的部分：把各专家对已见类别的概率取平均，达到校准阈值的样本直接给出已见类预测。  
剩下低置信样本进入候选池，把各专家的128维特征分别做L2归一化，再拼接起来交给HDBSCAN。  
它不要求预先填入“这一批必须有两个簇”。本文使用min_cluster_size=20、min_samples=10，由数据决定形成几个簇，同时允许有些样本暂时成为density noise。**

> **候选类别数$M$是已知的，数据簇数$\hat M$是不预设的，它们不必相等。**  
> **同一个故障组合可能形成多个簇，多个簇也可以被映射到同一个专家；本文没有强行做“一簇对应一类”的匹配。**  
> **但聚类本身只会把相似样本放在一起，它不会自动知道这团叫IB、那团叫OB。**

<!--
原文位置：§3.3.1–§3.3.3、式(12)–(15)，第5页；多对一映射见第6页。
-->

**给簇起名字，才是CRE真正关键的一步。  
最直观的办法是比较每个专家对整个簇的平均复合类置信度。但独立训练的模型，其softmax数值不一定能直接横向比较：一个专家报0.9，不见得就比另一个报0.8更可信。  
而且HUST的IB和OB都含有Ball，光靠这个共同成分很容易分不清。**

**所以文章又引入了一个很具体的物理签名：内圈与外圈基频带能量之比的对数。**

$$
r(x)=\log\frac{E_{\mathrm{BPFI}}(x)+\epsilon}{E_{\mathrm{BPFO}}(x)+\epsilon}
$$

**先用留出的合成验证数据，为IB和OB分别计算签名原型；再看测试簇的平均签名更接近哪一个。  
在HUST的簇级规则里，选中候选之后，只要其平均专家置信度达到阈值，或者物理签名足够接近对应原型，就接受该候选；都不满足的连贯簇可以保留为undefined anomaly。  
这就像先根据集体表现判断“大家更像内圈+滚动体这一组”，再用校准过的证据决定是否接受，而不是谁喊得响就听谁的。**

**HDBSCAN没能成簇的样本，也不能一股脑宣布异常。本文对density noise逐点检查候选置信度，不通过时回退到最有支持的已见类别。  
XJTU只有Mix一个候选，不需要IB/OB的能量比签名；它检查Mix置信度，不足时同样回到已见类，而不是把候选池里的所有样本都判成Mix。  
这些阈值只用已见验证数据和预留的合成验证数据确定，每份合成集合保留20%用于校准，不让真实未见故障来帮忙调门槛。**

<!--
原文位置：§3.3.3、式(15)–(18)、Algorithm 1，第5–6页。HUST簇级接受为“置信度条件或签名条件”；噪声点回退与单候选XJTU规则分别描述。
-->

**接下来看看实验。文章用了XJTU行星齿轮箱和HUST轴承两个平台，考的问题并不完全一样。  
XJTU以Ball、Inner、Outer三个单故障为已见类，以三者同时出现的Mix为唯一候选，重点考察高阶组合。HUST以N、B、I、O为已见类，以IB、OB为两个候选，重点考察共享Ball成分时能否分清不同组合。  
两个平台的候选语义不同：前者识别三成分的Mix，后者还要区分IB与OB。因此不能把所有复合故障都合成一个Unknown标签，再说已经完成了本文的组合识别任务。**

![XJTU行星齿轮箱与HUST轴承试验平台](images/blog13/testbeds.png)

<!--
图表占位 05｜XJTU行星齿轮箱与HUST轴承试验平台
使用原文：Fig. 3（PDF第7页）。
原文图／表题：Experimental testbeds for data acquisition. (a) XJTU planetary gearbox test rig. (b) HUST bearing simulator.
截取／替换说明：保留(a)、(b)两个平台及原图标注；本文正文只沿用论文的数据集与任务定义，不重新推定图中未使用的故障类别。
建议保存路径：images/blog13/testbeds.png
-->

![已见与候选未见类别及数据使用边界](images/blog13/class_roles.png)

<!--
图表占位 06｜已见与候选未见类别及数据使用边界
使用原文：Table 2（PDF第8页）。
原文图／表题：Class roles and permitted data use under the strict temporal protocol. “Syn. train/val” denotes PGCD-generated data, not real compound recordings.
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/class_roles.png
-->

<!--
原文位置：§4.1–§4.2.2、Fig. 3、Table 2，第6–8页。平台恒定转速均为1800 rpm；XJTU采样20.48 kHz，HUST采样51.2 kHz。
-->

**数据怎么分，也很重要。文章不是先把一整条信号切成窗口再随机打乱，而是先按时间分块：前60%训练，中间20%验证，最后20%测试。  
随后各块内部再切长度1024、步长1024的不重叠窗口，任何窗口都不能横跨分块边界；归一化均值和标准差也只从已见训练块计算。  
真实复合故障不参加训练、归一化或阈值校准。等模型与门槛都固定以后，测试末段的无标签特征才用于HDBSCAN-CRE，真实标签只负责最后算分。**

**注意最后这一句：它确实使用了当前测试批次的无标签特征，因此是transductive，而不是一个完全不看批次结构的独立单样本分类器。  
这不是偷偷用测试标签训练，但也不能把批次级校正的效果，写成“任意一个新样本到来，单个CNN立刻就能达到同样准确率”。**

![先按时间分块再切窗的数据协议](images/blog13/temporal_protocol.png)

<!--
图表占位 07｜先按时间分块再切窗的数据协议
使用原文：Fig. 4（PDF第8页）。
原文图／表题：Illustration of the strict temporal block splitting protocol designed to prevent data leakage and simulate realistic future-state industrial prediction.
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/temporal_protocol.png
-->

<!--
原文位置：§2、§4.2.1–§4.2.2，第2、7–8页。Table 3另列实际窗口数；本博客未把窗口数量解读成独立试验次数。
-->

**评估不能只报Unseen Accuracy，还要同时看Seen Accuracy。文章用两者的调和平均H-score来衡量平衡程度：**

$$
H=\frac{2A_sA_u}{A_s+A_u}
$$

**这就相当于两门课一起算成绩：一门接近满分、另一门几乎不会，不能被漂亮的单项分数掩盖。  
三个随机种子下，XJTU的已见准确率为95.93%±2.26%，未见准确率为98.97%±1.59%，H-score为97.42%±1.63%。  
HUST对应为95.50%±1.32%、94.50%±1.73%和95.00%±1.52%。这里的“±”是三次运行的样本标准差，不是置信区间。**

![PGCD-CRE广义零样本诊断主结果](images/blog13/main_results.png)

<!--
图表占位 08｜PGCD-CRE广义零样本诊断主结果
使用原文：Table 5（PDF第9页）。
原文图／表题：Revised-protocol GZSL results (mean ± sample standard deviation over three seeds).
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/main_results.png
-->

<!--
原文位置：§4.2.5、§4.3、Table 5，第9–10页。主结果均以Table 5的修订协议三种子统计为准。
-->

**不过，总分高不代表每个类别都一样稳。  
XJTU的Mix召回率达到98.97%，但精确率只有89.19%；也就是说，除了真正的Mix，大门还放进来了一些低置信已见样本。Outer的召回率为91.90%，是已见类里相对更难的一项。  
HUST这边，IB召回率为100%，OB是89.00%，Ball则是86.67%。剩余错误更集中在含Ball的类别边界，而不是所有类别均匀地掉一点。**

![两个平台的逐类Precision、Recall和F1](images/blog13/class_results.png)

<!--
图表占位 09｜两个平台的逐类Precision、Recall和F1
使用原文：Table 6（PDF第10页）。
原文图／表题：Per-class precision, recall, and F1 (%, mean ± sample standard deviation over three revised-protocol runs).
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/class_results.png
-->

**再看看混淆矩阵和t-SNE，可以更直观地理解类间关系。  
不过这里不要把图上的某一个百分比，直接拿来代替刚才的三次运行均值。论文明确将Fig. 5和Fig. 6作为定性特征视图，主结果与逐类统计仍应看Table 5和Table 6。  
特征图适合帮助理解“哪些类靠得近”，不适合单独证明完整分布已经对齐。**

![XJTU广义零样本诊断可视化](images/blog13/xjtu_visualization.png)

<!--
图表占位 10｜XJTU广义零样本诊断可视化
使用原文：Fig. 5（PDF第10页）。
原文图／表题：Visualization of GZSL results on the XJTU Gearbox Dataset.
截取／替换说明：保留混淆矩阵与t-SNE两部分。图中数值与Table 6的修订协议三种子汇总不逐项一致；按原文§4.3.1作为定性展示，不据此重算主结果。
建议保存路径：images/blog13/xjtu_visualization.png
-->

![HUST广义零样本诊断可视化](images/blog13/hust_visualization.png)

<!--
图表占位 11｜HUST广义零样本诊断可视化
使用原文：Fig. 6（PDF第11页）。
原文图／表题：Visualization of GZSL results on the HUST Bearing Dataset.
截取／替换说明：保留混淆矩阵与t-SNE两部分。主结果引用Table 5–6，图中单独显示的百分比不与三种子均值混用。
建议保存路径：images/blog13/hust_visualization.png
-->

<!--
原文位置：Table 6、§4.3.1及Fig. 5–6，第10–11页。此处沿用原文对定性图与统计结果的区分，不推定图对应哪个未注明的随机种子。
-->

**再跟其他方法比。文章给出了CE-GZSL、FREE、CSD-GZSL和Gating-AE的参考结果。  
XJTU上，Gating-AE的参考H-score是72.38%，PGCD-CRE为97.42%，数值差为25.04个百分点；HUST上则是94.31%与95.00%，只相差0.69个百分点。  
但论文同时交代，这些参考记录没有全部按同一个修订后的时间划分、种子集合和选模流程重新计算。因此前者是较大的描述性数值差，后者更适合说表现接近，不能都写成严格同协议下的显著领先。**

![XJTU与HUST通用GZSL基线参考对比](images/blog13/gzsl_baselines.png)

<!--
图表占位 12｜XJTU与HUST通用GZSL基线参考对比
使用原文：Table 7 与 Table 8（PDF第11页）。
原文图／表题：GZSL comparison on XJTU / GZSL comparison on HUST.
截取／替换说明：将同页Table 7和Table 8上下拼接为一张图；必须保留两表关于“reference results / revised three-seed protocol”的说明，不把不同协议包装成配对对比。
建议保存路径：images/blog13/gzsl_baselines.png
-->

**文章还列出了生成式和信号处理路线。比如XJTU上，ACGAN-FG、VAE-GAN、TMCGAN的参考未见准确率分别为42.07%、60.70%和72.24%；VMD-CE-GZSL等信号处理混合方案则说明，提取可解释特征之后，仍然需要一个能处理未见语义的映射。  
这些表能提供方法定位，但不能仅凭结果差距就断言“GAN发生了模式崩塌”或“Diffusion已经复原了真实传递过程”。原文并没有直接验证这些因果解释。**

![生成式与信号处理混合基线参考对比](images/blog13/alternative_baselines.png)

<!--
图表占位 13｜生成式与信号处理混合基线参考对比
使用原文：Table 9 与 Table 10（PDF第12页）。
原文图／表题：Generative-paradigm comparison on XJTU / Performance against SP-based hybrid baselines on XJTU.
截取／替换说明：将同页两表上下拼接，保留表题。Table 9与修订PGCD-CRE的差异为描述性比较；两表不能替代后文同协议消融。
建议保存路径：images/blog13/alternative_baselines.png
-->

<!--
原文位置：§5.1–§5.3、Table 7–10，第10–12页。不同协议记录不用于宣称配对显著性或单模块因果贡献。
-->

**真正值得仔细看的，是后面的消融。先把CRE拿掉，只比较生成器，再让相同的逐样本共享CNN去分类。  
Raw Signal Mixup的未见准确率只有7.20%±0.99%；分别用one-hot DDPM生成再混合，也只有9.10%±8.29%。  
换成组合条件之后，均值升到18.50%；加入等权物理引导后是20.41%；使用传播路径权重后是27.61%±28.62%。**

**等等，完整系统不是接近99%吗？  
没错，但这张表刻意不使用CRE。它说明组合条件和物理引导的均值呈改善趋势，同时也说明生成器单独带来的迁移效果很不稳定，28.62个百分点的标准差不能当作没看见。  
因此不能把最终的98.97%全记在“扩散模型生成得逼真”这一项上。生成候选训练数据，和把真实测试批次正确识别出来，中间还有很长一段路。**

![不使用CRE时的生成器消融](images/blog13/generation_ablation.png)

<!--
图表占位 14｜不使用CRE时的生成器消融
使用原文：Table 11（PDF第13页）。
原文图／表题：Revised-protocol XJTU generation ablation with a pointwise shared 1D-CNN (mean ± sample standard deviation over seeds 0–2).
截取／替换说明：完整保留均值与标准差，并保留“pointwise shared 1D-CNN”条件；不要把Full PGCD-CRE主结果追加为同设置的一行。
建议保存路径：images/blog13/generation_ablation.png
-->

<!--
原文位置：§5.4.1、Table 11，第12–13页。同组使用相同共享CNN、合成样本数量、时间划分和训练日程。
-->

**HUST的诊断策略消融更直接。统一分类器的已见准确率为99.17%，但未见准确率为0；两个专家直接平均概率，未见准确率也只有0.67%。  
即使先用HDBSCAN聚类、再只靠置信度命名，未见准确率仍然是0。也就是说，样本聚到一起了，并不代表IB和OB的名字就能贴对。  
加入候选特定的物理频带比签名后，语义对应才恢复。这里的CRE不是简单投票，而是置信度、物理签名和校准规则共同起作用。**

**不过，HDBSCAN也不是包赢。干净数据上，固定$K=2$的K-Means加相同CRE，未见准确率同样达到94.50%，H-score为94.42%。  
完整PGCD-CRE的H-score是95.00%；移除density-noise fallback时，未定义比例为0.78%，加回后降为0，同时已见准确率提高1.17个百分点，未见均值保持不变。  
所以这组结果更能说明语义校正与回退规则的重要性，而不是证明“只要换成HDBSCAN，就一定比K-Means更准”。**

![HUST专家融合与语义校正策略消融](images/blog13/diagnostic_ablation.png)

<!--
图表占位 15｜HUST专家融合与语义校正策略消融
使用原文：Table 12（PDF第13页）。
原文图／表题：Revised-protocol HUST diagnostic ablation (mean ± sample standard deviation over seeds 0–2).
截取／替换说明：完整保留Unified classifier、Probability averaging、K-Means+CRE、confidence-only、无noise fallback及Full各行，以及Undefined列。
建议保存路径：images/blog13/diagnostic_ablation.png
-->

<!--
原文位置：§5.4.2、Table 12，第13页。K-Means的K=2属于该消融设置；完整方法不预设测试簇数。
-->

**那加噪之后呢？这次结果没有继续维持一个“所有曲线都很漂亮”的故事。  
文章只在测试窗口中加入AWGN，信噪比从10 dB降到−10 dB，验证阈值和聚类超参数保持不变，每个噪声水平重新聚类。  
更新后的结果没有显示两种聚类规则中谁始终更稳。在−2 dB时，两者H-score都只剩2.18%±3.78%；到−4 dB，两者均降为0。**

**原因不能简单归结成“聚类器不够强”：噪声首先影响的是专家特征、已见筛选和用于命名的物理签名，这几步出了问题，后面再怎么分簇也未必救得回来。  
因此，不能把HDBSCAN能输出density noise，直接等同于整套系统已经具有强噪声鲁棒性。低信噪比运行仍然是本文明确暴露的限制。**

![K-Means-CRE与HDBSCAN-CRE的AWGN测试](images/blog13/noise_robustness.png)

<!--
图表占位 16｜K-Means-CRE与HDBSCAN-CRE的AWGN测试
使用原文：Fig. 7（PDF第14页）。
原文图／表题：Updated AWGN robustness of K-Means-CRE and HDBSCAN-CRE on HUST: (a) unseen accuracy and (b) H-score.
截取／替换说明：保留两幅子图和三种子的均值±标准差阴影；同时呈现Unseen Accuracy与H-score，避免只展示单项较高的曲线。
建议保存路径：images/blog13/noise_robustness.png
-->

<!--
原文位置：§5.4.3、Fig. 7，第13–14页。上述失效条件限定为论文给出的测试时AWGN设置。
-->

**再回到生成信号本身。Fig. 8把真实Mix和合成Mix的时域波形、包络谱放在一起，能看到示例中相似的冲击和调制结构，以及标注特征频带附近的能量。  
这种图很适合解释“物理引导到底在关注什么”，但看着像，并不等于整个概率分布就一样，更不等于真实机械传递机制被还原了。**

![真实与合成Mix的时域波形及包络谱](images/blog13/signal_fidelity.png)

<!--
图表占位 17｜真实与合成Mix的时域波形及包络谱
使用原文：Fig. 8（PDF第15页）。
原文图／表题：Qualitative comparison of Real vs. Synthetic “Mix” compound fault signals from the XJTU dataset.
截取／替换说明：保留(a)–(d)四个子图，以及BSF/BPFI/BPFO标线；这是定性示例，不作为全分布保真证明。
建议保存路径：images/blog13/signal_fidelity.png
-->

**所以文章又做了一个evaluation-only审计：在归一化的对数包络功率谱上算合成与真实数据的$\mathrm{MMD}^2$，越小表示在这个描述空间中越接近。  
XJTU Mix为0.01586±0.00077，HUST IB为0.03171±0.00988，HUST OB为0.01672±0.00293。  
这些真实复合故障数据是在训练结束后才进入评估的，不会反过来参与训练或挑选阈值。**

![合成与真实复合故障包络谱分布审计](images/blog13/spectrum_audit.png)

<!--
图表占位 18｜合成与真实复合故障包络谱分布审计
使用原文：Table 13（PDF第15页）。
原文图／表题：Synthetic–real envelope-spectrum MMD² (lower is closer; mean ± sample standard deviation over three seeds).
截取／替换说明：保留完整图／表及图例；不必截入周围正文。
建议保存路径：images/blog13/spectrum_audit.png
-->

**而且，这个审计并不是每一类都支持“物理引导后全面变好”。在seed-0的配对检查中，HUST IB的完整包络谱距离从粗混合的0.03675变成PGCD的0.04296，反而变大；与此同时，它的目标频带物理损失却下降了。  
这恰好说明：目标频带更符合设计意图，不等于整个包络谱都更接近真实数据。  
同样，Table 11对应的组合扩散、等权引导和传播权重引导，其MMD数值非常接近，不能仅据此宣称传播权重带来了稳定的全谱对齐优势。**

<!--
原文位置：§5.5–§5.6、Fig. 8、Table 13，第14–15页；生成变体MMD比较见§5.4.1，第13页。
-->

**顺便一提，时间分块虽然避免了窗口混入不同集合，却不保证前后的数据分布完全相同。  
Table 14对已见训练段与测试段做了时序分布审计。XJTU的Inner和Outer仍能被域分类器部分区分，方向无关AUC分别约为0.670和0.618，说明有可测的时间漂移。  
所以，严格划分解决的是“别把考题混进训练里”，不是保证“考试环境永远和训练环境一样”。**

![已见训练与测试块的时序分布差异](images/blog13/temporal_drift.png)

<!--
图表占位 19｜已见训练与测试块的时序分布差异
使用原文：Table 14（PDF第16页）。
原文图／表题：Seen-train versus seen-test temporal-distribution audit.
截取／替换说明：保留MMD²与AUC*两列及表注；表中的小幅负无偏MMD²估计按原样保留，不改成负的总体距离或擅自改写为零。
建议保存路径：images/blog13/temporal_drift.png
-->

<!--
原文位置：§5.6、Table 14，第15–16页。AUC*=max(AUC,1−AUC)，0.5为机会水平。
-->

**再看引导强度$s$。是不是物理引导越强，效果越好？也没有这么简单。  
文章在预设$s=10$之外，额外扫描了0到20的多个设置，每个设置、每个种子生成300条XJTU Mix样本。完整CRE的H-score大体处在平台区：$s=0$时为98.65%，$s=10$时为98.73%，$s=20$时为98.54%，$s=12.5$附近有一次更明显的波动。  
这里的结果属于独立敏感性设置，不能拿98.73%去替换主实验Table 5的97.42%。它支持的是完整CRE在这组参数范围内相对稳定，而不是证明10是唯一最优值，或者物理引导单独决定了全部增益。**

![物理引导尺度敏感性分析](images/blog13/guidance_sensitivity.png)

<!--
图表占位 20｜物理引导尺度敏感性分析
使用原文：Fig. 9（PDF第16页）。
原文图／表题：Guidance-scale sensitivity on XJTU: (a) H-score for the pointwise shared CNN and full CRE, and (b) synthetic–real envelope-spectrum MMD².
截取／替换说明：保留两幅子图、误差带和s=10虚线。该扫描每设置每种子生成300条Mix，是独立的事后敏感性实验。
建议保存路径：images/blog13/guidance_sensitivity.png
-->

<!--
原文位置：§5.7、Fig. 9，第15–16页。扫描不用于模型选择；完整CRE与逐点共享CNN分别统计。
-->

**最后看看部署。扩散模型比较重，但它负责离线生成，不是每来一条传感器信号都现场跑120或150步。  
论文给出的U-Net参数量为12.66M，一步约1.5587 GFLOPs；完整XJTU、HUST生成分别约187.04和233.81 GFLOPs/样本。单个诊断专家只有0.33M参数，计算量约0.0162 GFLOPs。  
不过，轻量专家不等于完整系统已经达到固定毫秒级实时诊断。**

**Table 15里的单专家1.05 ms、两个HUST专家顺序运行2.10 ms，来自原始提交版本的RTX 4090计时参考。修订实验使用GTX 1050 Ti，但没有重新做受控延迟测试。  
HDBSCAN和CRE还依赖缓存批次大小，不能直接塞进一个固定的单样本FLOPs或延迟数字。  
更符合本文设计的部署方式是：离线生成、逐样本提取专家特征、缓存一小批后周期性做语义校正，而不是把它描述成已经验证的全流程逐点实时系统。**

![模块计算量与历史计时参考](images/blog13/computational_cost.png)

<!--
图表占位 21｜模块计算量与历史计时参考
使用原文：Table 15（PDF第17页）。
原文图／表题：Architecture cost and original-submission RTX 4090 timing reference for core modules.
截取／替换说明：完整保留表题中的“original-submission RTX 4090 timing reference”及HDBSCAN+CRE的batch-dependent一行，避免把历史计时当成修订环境的端到端实测。
建议保存路径：images/blog13/computational_cost.png
-->

<!--
原文位置：§5.8、Table 15，第16–17页。架构计算量与历史硬件计时分别表述。
-->

**综合来讲，这篇文章的亮点不只是“用Diffusion生成复合故障”。  
它把两种不确定性拆开处理：没有真实复合训练样本时，用组合条件和特征频带先验构造候选数据；面对合成到真实的偏移时，再借助批次结构、专家置信度和物理签名进行语义校正。  
从消融结果看，后半段尤其不能省略。一个看起来合理的生成器，并不会自动带来一个可靠的零样本诊断器。**

**但适用边界也很清楚：候选字典和专家数量必须预先指定，CRE需要批次或短缓存，传播路径系数仍是固定经验先验。  
目前三个种子只能提供初步的波动估计；生成器单独使用时方差很大，强AWGN下完整流程也会失效。  
另外，实验覆盖的是两个恒定转速平台，不能把这些结果直接推广成对变转速、负载变化、传感器换位和任意未定义故障都可靠。**

**所以我个人更愿意把PGCD-CRE理解成一种“有候选、有物理线索、也有测试时校正”的组合诊断路线。  
不是让模型从没见过的数据里凭空猜答案，而是先把工程上可能出现的组合写清楚，再让生成模型提供训练支撑，最后用真实无标签批次检查这些候选到底是否站得住。  
这种思路的价值，在于把“我知道有哪些组合可能发生”和“我知道这一批实际发生了什么”分开，而不是把两者混成一句零样本万能识别。**

<!--
原文位置：§6，第17页。总结沿用论文的候选字典、传导推理、固定权重、有限重复与恒转速评估边界。
-->

**以上就是这篇文章的主要内容。论文提供的代码仓库地址为：  
`https://github.com/Harmonican97/Physics-Guided-Causal-Diffusion-with-Confidence-Rectified-Ensemble`  
网址中保留了历史命名Causal，但论文方法是Compositional，原文的数据可用性说明也明确表示它不是正式的因果推断模型。  
如果你关注复合故障、广义零样本诊断、扩散生成或者物理引导学习，可以进一步查看论文的公式、消融和评估流程；如果相关内容对你的研究有帮助，也欢迎引用这项工作。**

<!--
原文位置：Data availability，第17页。仓库地址按论文原样保留，未把其当前在线状态作为额外验证结果；原始数据需遵循原数据集许可。
-->

[看看上一篇](#blog12) | [返回目录](#work) | [看看下一篇](#blog_occupy)

<!--
blog13 图表替换索引（仅源码可见；PDF页码从首页起算）
01. images/blog13/cover.jpg ← 论文首页，PDF第1页；PGCD-CRE论文封面
02. images/blog13/framework.png ← Fig. 1，PDF第3页；PGCD-CRE整体框架
03. images/blog13/compositional_diffusion.png ← Fig. 2，PDF第4页；物理引导组合扩散结构
04. images/blog13/frequency_weights.png ← Table 4，PDF第9页；特征频率与固定传播路径权重
05. images/blog13/testbeds.png ← Fig. 3，PDF第7页；XJTU行星齿轮箱与HUST轴承试验平台
06. images/blog13/class_roles.png ← Table 2，PDF第8页；已见与候选未见类别及数据使用边界
07. images/blog13/temporal_protocol.png ← Fig. 4，PDF第8页；先按时间分块再切窗的数据协议
08. images/blog13/main_results.png ← Table 5，PDF第9页；PGCD-CRE广义零样本诊断主结果
09. images/blog13/class_results.png ← Table 6，PDF第10页；两个平台的逐类Precision、Recall和F1
10. images/blog13/xjtu_visualization.png ← Fig. 5，PDF第10页；XJTU广义零样本诊断可视化
11. images/blog13/hust_visualization.png ← Fig. 6，PDF第11页；HUST广义零样本诊断可视化
12. images/blog13/gzsl_baselines.png ← Table 7 与 Table 8，PDF第11页；XJTU与HUST通用GZSL基线参考对比
13. images/blog13/alternative_baselines.png ← Table 9 与 Table 10，PDF第12页；生成式与信号处理混合基线参考对比
14. images/blog13/generation_ablation.png ← Table 11，PDF第13页；不使用CRE时的生成器消融
15. images/blog13/diagnostic_ablation.png ← Table 12，PDF第13页；HUST专家融合与语义校正策略消融
16. images/blog13/noise_robustness.png ← Fig. 7，PDF第14页；K-Means-CRE与HDBSCAN-CRE的AWGN测试
17. images/blog13/signal_fidelity.png ← Fig. 8，PDF第15页；真实与合成Mix的时域波形及包络谱
18. images/blog13/spectrum_audit.png ← Table 13，PDF第15页；合成与真实复合故障包络谱分布审计
19. images/blog13/temporal_drift.png ← Table 14，PDF第16页；已见训练与测试块的时序分布差异
20. images/blog13/guidance_sensitivity.png ← Fig. 9，PDF第16页；物理引导尺度敏感性分析
21. images/blog13/computational_cost.png ← Table 15，PDF第17页；模块计算量与历史计时参考
-->

<!--
格式说明：与HTML正文一一对应；行内公式使用$...$，独立公式使用$$...$$。图表说明与原文定位保留为HTML注释，不显示在博客正文。
-->
'''


def main() -> None:
    base = Path(__file__).resolve().parent

    # 使用新目录，避免覆盖已有文件。
    output_dir = base / "blog13_local"
    index = 1
    while output_dir.exists():
        index += 1
        output_dir = base / ("blog13_local_" + str(index))

    markdown = MARKDOWN.strip() + "\n"
    html = to_html(markdown)

    if html.count('<span class="image main">') != 21:
        raise ValueError("图表占位数量不完整，请重新复制完整代码。")

    output_dir.mkdir()

    for filename, content in (
        ("blog13.md", markdown),
        ("blog13.html", html),
    ):
        with (output_dir / filename).open(
            "w", encoding="utf-8", newline="\n"
        ) as file:
            file.write(content)

    print("已生成：", output_dir / "blog13.html")
    print("已生成：", output_dir / "blog13.md")
    print("21处图表占位、原文编号、页码和替换说明均已保留。")


if __name__ == "__main__":
    main()