# 智能型艾瑟雅（IntelligentIthea）
<div align=center><img src="https://app.xgnd.net/4_G7WH4NB3WX_8J_HQ4R9_J.png" width="20%"/>

**智能型艾瑟雅（IntelligentIthea）：一个终末三问（末日时在做什么？有没有空？可以来拯救吗？）抽卡游戏qq机器人**
<p align=center><a href="https://qm.qq.com/cgi-bin/qm/qr?k=45tg4hcuhjbxHT8u9QIDhVV_Ne6zTzJr&jump_from=webapi"><img src="https://img.shields.io/badge/qq%E7%BE%A4-768887710-orange?style=flat-square" alt="QQ Chat"></a></p>
</div>

>**本机器人基于[NoneBot2](https://github.com/nonebot/nonebot2)制作，衷心服务于每一位热爱珂学的珂学家！**  
>**十分感谢各位开发组的小伙伴：青风光翼（285984384）、西瓜nd（2741584344）、回响（2769640073）**  
>**也十分感谢一直以来陪伴我们各位珂学家！**
## 功能
### 1、抽卡游戏（共包含以下命令）
抽卡：玩家可以通过输入“抽卡”或戳一戳（双击机器人头像）完成抽卡。机器人会随机抽取普通至超稀有之间的2张至4张之间的卡牌
排行榜：按本群玩家图鉴数进行排行的排行榜

合成 [角色] [角色]：玩家可以通过输入“合成”+空格+角色名（或角色编号）+空格+角色名（或角色编号）完成合成。但注意，合成的卡牌必须是同一等级的哟！

一键合成 [等级]：玩家可以通过输入“合成”+空格+等级名（普通、稀有、超稀有）完成一键合成。一键合成只会合成多余的卡，也就是卡牌数大于等于两张的卡牌的多余卡牌，会自动留下一张卡以保证图鉴不失，所以请放心使用（当然如果你喜欢作死把所有卡都合成了，一键合成可能就不太适合你了...）

查看 [角色]：玩家可以通过输入“合成”+空格+角色名（或角色编号）查看角色。前提是你必须拥有该角色

查看仓库：当玩家输入“查看仓库”后，就可以查看到自己的持有卡片总数、超稀有卡片数、稀有卡片数、普通卡片数、图鉴完成度、当前群排名

卡牌列表：查看所有卡牌的名字

编号图：查看所有卡牌对应编号的图片

兑换 [商品]：玩家可以通过输入“兑换”+空格+商品名兑换商品。或直接输入“兑换”查看商品名后再输入商品名完成兑换

### 2、1A2B（共包含以下命令）
1A2B规则：发送“1A2B规则”阅读游戏规则

1A2B开始：发送“1A2B开始”开始游戏

1A2B结束：发送“1A2B结束”结束游戏

### 3、走进珂学
珂学：随机返图或一句经典台词或一条终末的科普

珂图 n：获取n张图片，n可为空

珂言：获取一句经典台词

珂普：获取一条终末的科普

查看图片 k：查看编号为k的图片

图库状态：查看图库状态

提示：使用以上指令获取的图片是缩略图哦

如要获取高清版，请访问https://img.sukasuka.cn/post/图片id

### 4、一言
随机发送一条动画、漫画、游戏、文学领域中的经典台词
### 5、点歌 [歌曲名]
此为原插件[songpicker2](https://github.com/maxesisn/nonebot_plugin_songpicker2)稍加改动而成。玩家可以通过输入“点歌”+空格+歌曲名完成点歌。仅支持网易云音乐的点歌（因为实在找不到其他音乐平台的接口或接口经常失灵）
### 6、赛跑
此为原插件[Pcr_Run](https://github.com/Rs794613/PcrRun)稍加改动而成。一个赛跑下注的小游戏，玩家可以发起赛跑并进行墨鱼币下注。注：nonebot2更新后的新特性，导致赛跑的发起人无法参与下注
### 7、闲聊
此为原插件[ELFChatBot](https://github.com/Quan666/ELFChatBot)稍加改动而成。玩家可在群里@机器人发起会话，发送“再见”结束会话或通过私聊直接进行闲聊
### 8、五子棋
五子棋开始：创建一个棋局（持续60s），等待其他玩家加入

五子棋加入：加入一个等待阶段的棋局

认输：当玩家正在棋局中时，可用此命令结束棋局



## 用法
### 官方机器人环境（仅供参考）：
- 语言：python 3.8.5
- 框架：[nonebot 2.0.0a16](https://github.com/nonebot/nonebot2)
- 适配器：[nonebot-adapter-cqhttp 2.0.0a16](https://pypi.org/project/nonebot-adapter-cqhttp/2.0.0a16/)
- QQ协议端：[go-cqhttp v1.0.0-beta8](https://github.com/Mrs4s/go-cqhttp)
- 服务器：Windows Server 2016 64位数据中心版
### 部署：
请参考[NoneBot2指南](https://v2.nonebot.dev/guide/)

注：插件不兼容v2.0.0-beta.1及以上版本的框架和适配器

## 友情链接
#### [中国珂学院](https://wiki.sukasuka.cn/chtholly.ac.cn/)
#### [中珂院维基](https://wiki.sukasuka.cn/)
#### [中珂院图库](https://img.sukasuka.cn/)
