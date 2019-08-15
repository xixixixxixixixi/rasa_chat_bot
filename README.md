# rasa_chat_bot
## 一个小小的股票查询机器人<br> 
## 说明：
* 主函数为main1.py<br> 
## 总体思路：<br> 
### * 整体上：
  * 程序的整体逻辑上分为登录前和登录后两个部分，用到的主要工具有spacy，rasa_nlu，和telegram。<br> 
  * 在登录前，可以和机器人进行一些闲聊等不涉及股票数据上的交流，闲聊通过固定套路和意图识别并回复的方式来<br> 
  实现。<br> 
  * 在登录完成后，用户可以通过多轮查询来查询自己所需要的信息，由于本项目查询的信息都是基于特定股票的，因此对于
  大部分的查询都需要先选定自己想查询的股票，然后才能进行后续操作。<br>
### * 推荐股票：
  * 对股票不熟悉的用户，可以首先让机器人给自己推荐一些股票，这部分的推荐是通过意图识别，抽取查询的实体，然后通过查询本地数据库来实现的。由于本地数据库，因此可以根据数据库的内容来设置一些推荐算法，这部分可以由开发者自行开发。<br> 
### * 查询信息：
  * 在得知了自己想查询的股票后，用户可以通过多轮查询数据，由于这部分的查询都偏向格式化，因此意图识别和实体抽取
  整合为一个了部分，通过rasa_nlu中的实体抽取功能直接抽取。<br> 
  * 其中对于历史价格，由于文本的回复方式比较抽象，因此处理json串生成表格通过文件方式发送给用户。<br> 
### * 语音查询：
  * 为了更加方便用户的操作，此项目中包含了语音查询的功能，用户不需要显式的声明查询模式，若需要语音查询，则直接通过telegram的发送语音信息按钮即可进行查询。<br> 
  * 注意：语音转文字部分使用的是百度api，由于telegram需要科学上网，但对于百度的接口，圈内圈外的请求速度相差太过悬殊，因此这部分正考虑换成国外的语音接口。<br> 
### * 整合telegram：
  * 本项目使用telegram的方法来实现机器人与用户间的交互。
  * 国内用户使用时需要科学上网。
  * 备注：使用ss的方式仍然会导致错误，因为即便搭建了ss，开启了全局模式，在使用股票数据接口时仍然会请求失败，这是因为在全局ss模式下，虽然浏览器的访问方式改为了你设置的ss代理服务器，但是python等软件的访问方式仍然默认为你的原有网络，而在telegram的函数中，相关代理设置不容易修改，因此国内用户请找到一个适合自己的科学上网工具。
