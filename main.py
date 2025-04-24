import asyncio
import random
from time import sleep
from astrbot.api.event import filter, AstrMessageEvent, MessageEventResult
from astrbot.api.star import Context, Star, register
from astrbot.api import logger
from astrbot.core.platform.sources.aiocqhttp.aiocqhttp_message_event import AiocqhttpMessageEvent
from astrbot.api import AstrBotConfig

emoji_list = [
    # 系统表情（type=1，ID为数字，存储为整数）
    4, 5, 8, 9, 10, 12, 14, 16, 21, 23, 24, 25, 26, 27, 28, 29, 30, 32, 33, 34,
    38, 39, 41, 42, 43, 49, 53, 60, 63, 66, 74, 75, 76, 78, 79, 85, 89, 96, 97,
    98, 99, 100, 101, 102, 103, 104, 106, 109, 111, 116, 118, 120, 122, 123, 124,
    125, 129, 144, 147, 171, 173, 174, 175, 176, 179, 180, 181, 182, 183, 201,
    203, 212, 214, 219, 222, 227, 232, 240, 243, 246, 262, 264, 265, 266, 267,
    268, 269, 270, 271, 272, 273, 277, 278, 281, 282, 284, 285, 287, 289, 290,
    293, 294, 297, 298, 299, 305, 306, 307, 314, 315, 318, 319, 320, 322, 324, 326,
    # emoji表情（type=2，ID为文档中明确的数字编号，存储为字符串）
    '9728', '9749', '9786', '10024', '10060', '10068', '127801', '127817', '127822',
    '127827', '127836', '127838', '127847', '127866', '127867', '127881', '128027',
    '128046', '128051', '128053', '128074', '128076', '128077', '128079', '128089',
    '128102', '128104', '128147', '128157', '128164', '128166', '128168', '128170',
    '128235', '128293', '128513', '128514', '128516', '128522', '128524', '128527',
    '128530', '128531', '128532', '128536', '128538', '128540', '128541', '128557',
    '128560', '128563'
]

@register("astrbot_qqemotionreply", "QiChen", "让bot给消息回应表情", "1.0.0")
class MyPlugin(Star):
    def __init__(self, context: Context, config: AstrBotConfig):
        super().__init__(context)
        #读取配置文件
        self.config = config
        self.default_emoji_num=config.get('default_emoji_num')
        self.time_interval=config.get('time_interval')
        self.open_admin_mode=config.get('open_admin_mode')
    
    #使用指令的方式贴表情
    @filter.command("贴表情", alias={'fill', '贴'})
    async def replyMessage(self, event: AstrMessageEvent,emojiNum:int=-1):
        #如果用户未输入参数,读取配置文件默认值
        if emojiNum==-1:
            emojiNum=self.default_emoji_num

        replyID=await self.get_reply_id(event)
        receiverID=await self.get_receiver_id(event)

        #管理员无法选中逻辑
        if self.open_admin_mode:
            #TODO:逻辑暂未实现
            pass
        
        if(emojiNum>20):
            emojiNum=20
            yield event.plain_result("贴表情数量超出上限,已设为20")

        if replyID:
            # 调用贴表情函数，这里可以传入不同的表情 ID
            #随机发送指定数量的表情
            rand_emoji_list=random.sample(emoji_list,emojiNum)
            for id in rand_emoji_list:
                await self.send_emoji(event, replyID, id)
                #防止请求过于密集
                sleep(self.time_interval)
    
    @filter.command("erhelp", alias={'贴表情帮助', '表情帮助'})
    async def showHelp(self,event:AstrMessageEvent):
        help_text="""
贴表情使用方法:/贴表情 表情数量(不超过20)
--指令别名/fill /贴
"""
        yield event.plain_result(help_text)

    #获取转发消息id
    async def get_reply_id(self,event):
        message_chain = event.message_obj.message
        # 获取转发消息的消息 ID
        replyID = None
        for message in message_chain:
            if message.type == "Reply":
                replyID = message.id
                break
        return replyID
    
    #获取接收者id
    async def get_receiver_id(self,event):
        message_chain = event.message_obj.message
        #获取接收者id
        receiverID=None
        for message in message_chain:
            if message.type=="Reply":
                receiverID=message.sender_id
                break
        logger.info(f"===接收者ID:{receiverID}===")
        return receiverID


    async def send_emoji(self, event, message_id, emoji_id):
        # 调用 napcat 的 api 发送贴表情请求
        if event.get_platform_name() == "aiocqhttp":
            # qq
            assert isinstance(event, AiocqhttpMessageEvent)
            client = event.bot  # 得到 client
            payloads = {
                "message_id": message_id,
                "emoji_id": emoji_id,
                "set": True
            }
            ret = await client.api.call_action('set_msg_emoji_like', **payloads)  # 调用 协议端  API
            logger.info(f"表情ID:{emoji_id}")
            logger.info(f"贴表情返回结果: {ret}")
            post_result = ret['result']
            if post_result == 0:
                logger.info("请求贴表情成功")
            elif post_result == 65002:
                logger.error("已经回应过该表情")
            elif post_result == 65001:
                logger.error("表情已达上限，无法添加新的表情")
            else:
                logger.error("未知错误")

    