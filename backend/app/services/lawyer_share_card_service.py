"""律师分享卡片生成服务"""
from datetime import datetime
from typing import Literal
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..models.lawfirm import Lawyer, LawFirm
from ..models.user import User


class LawyerShareCardService:
    """律师分享卡片服务"""

    # 卡片模板类型
    TEMPLATE_SIMPLE = "simple"  # 简洁模板
    TEMPLATE_PROFESSIONAL = "professional"  # 专业模板
    TEMPLATE_ELEGANT = "elegant"  # 优雅模板

    # 卡片尺寸
    CARD_WIDTH = 800
    CARD_HEIGHT = 400

    @staticmethod
    def _get_template_colors(template: str) -> dict[str, tuple[int, int, int]]:
        """获取模板配色方案"""
        colors = {
            LawyerShareCardService.TEMPLATE_SIMPLE: {
                "background": (255, 255, 255),
                "primary": (59, 130, 246),  # 蓝色
                "secondary": (107, 114, 128),  # 灰色
                "text": (17, 24, 39),  # 深色
                "text_light": (107, 114, 128),  # 浅色
                "accent": (251, 191, 36),  # 金色
            },
            LawyerShareCardService.TEMPLATE_PROFESSIONAL: {
                "background": (30, 41, 59),  # 深蓝灰色
                "primary": (59, 130, 246),  # 蓝色
                "secondary": (148, 163, 184),  # 浅灰色
                "text": (241, 245, 249),  # 白色
                "text_light": (148, 163, 184),  # 浅灰色
                "accent": (251, 191, 36),  # 金色
            },
            LawyerShareCardService.TEMPLATE_ELEGANT: {
                "background": (248, 250, 252),  # 浅灰白色
                "primary": (99, 102, 241),  # 靛蓝色
                "secondary": (156, 163, 175),  # 灰色
                "text": (31, 41, 55),  # 深色
                "text_light": (107, 114, 128),  # 浅色
                "accent": (236, 72, 153),  # 粉色
            },
        }
        return colors.get(
            template, colors[LawyerShareCardService.TEMPLATE_SIMPLE])

    @staticmethod
    def _draw_rounded_rectangle(
        draw,
        xy: tuple[int, int, int, int],
        radius: int = 10,
        fill: tuple[int, int, int] | None = None,
        outline: tuple[int, int, int] | None = None,
        width: int = 1,
    ):
        """绘制圆角矩形"""
        from PIL import Image, ImageDraw

        x1, y1, x2, y2 = xy
        if radius > 0:
            # 绘制圆角矩形
            draw.rounded_rectangle(
                xy,
                radius=radius,
                fill=fill,
                outline=outline,
                width=width,
            )
        else:
            # 绘制普通矩形
            draw.rectangle(
                xy,
                fill=fill,
                outline=outline,
                width=width,
            )

    @staticmethod
    def _draw_star(draw, center: tuple[int, int],
                   size: int, color: tuple[int, int, int]):
        """绘制五角星"""
        import math

        cx, cy = center
        points = []
        for i in range(10):
            angle = math.pi / 5 * i - math.pi / 2
            r = size if i % 2 == 0 else size / 2
            x = cx + r * math.cos(angle)
            y = cy + r * math.sin(angle)
            points.append((x, y))
        draw.polygon(points, fill=color)

    @staticmethod
    def _wrap_text(text: str, font, max_width: int) -> list[str]:
        """文本换行"""
        from PIL import ImageFont

        lines = []
        words = text.split()
        current_line = ""

        for word in words:
            test_line = current_line + word + " " if current_line else word
            bbox = font.getbbox(test_line)
            width = bbox[2] - bbox[0]

            if width <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line.strip())
                current_line = word + " "

        if current_line:
            lines.append(current_line.strip())

        return lines

    @staticmethod
    async def generate_card(
        db: AsyncSession,
        lawyer_id: int,
        template: Literal["simple", "professional", "elegant"] = "simple",
    ) -> bytes:
        """
        生成律师分享卡片

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            template: 卡片模板类型

        Returns:
            卡片图片的字节数据（PNG格式）
        """
        from PIL import Image, ImageDraw, ImageFont
        import io

        # 获取律师信息
        lawyer_result = await db.execute(
            select(Lawyer).where(Lawyer.id == lawyer_id)
        )
        lawyer = lawyer_result.scalar_one_or_none()
        if not lawyer:
            raise ValueError("律师不存在")

        # 获取律所信息
        firm_name = None
        if lawyer.firm_id:
            firm_result = await db.execute(
                select(LawFirm).where(LawFirm.id == lawyer.firm_id)
            )
            firm = firm_result.scalar_one_or_none()
            if firm:
                firm_name = firm.name

        # 获取用户信息
        user_result = await db.execute(
            select(User).where(User.id == lawyer.user_id)
        )
        user = user_result.scalar_one_or_none()

        # 获取配色方案
        colors = LawyerShareCardService._get_template_colors(template)

        # 创建画布
        img = Image.new(
            "RGB",
            (LawyerShareCardService.CARD_WIDTH,
             LawyerShareCardService.CARD_HEIGHT),
            colors["background"])
        draw = ImageDraw.Draw(img)

        # 尝试加载字体
        try:
            # 尝试使用系统字体
            title_font = ImageFont.truetype("msyh.ttc", 36)  # 微软雅黑
            name_font = ImageFont.truetype("msyhbd.ttc", 48)  # 微软雅黑粗体
            text_font = ImageFont.truetype("msyh.ttc", 20)
            small_font = ImageFont.truetype("msyh.ttc", 16)
        except Exception:
            # 回退到默认字体
            title_font = ImageFont.load_default()
            name_font = ImageFont.load_default()
            text_font = ImageFont.load_default()
            small_font = ImageFont.load_default()

        # 绘制装饰元素
        if template == LawyerShareCardService.TEMPLATE_SIMPLE:
            # 简洁模板：左侧蓝色条
            LawyerShareCardService._draw_rounded_rectangle(
                draw,
                (0, 0, 8, LawyerShareCardService.CARD_HEIGHT),
                radius=0,
                fill=colors["primary"],
            )
            # 底部装饰线
            LawyerShareCardService._draw_rounded_rectangle(
                draw,
                (20,
                 LawyerShareCardService.CARD_HEIGHT - 20,
                 LawyerShareCardService.CARD_WIDTH - 20,
                 LawyerShareCardService.CARD_HEIGHT - 16),
                radius=2,
                fill=colors["primary"],
            )

        elif template == LawyerShareCardService.TEMPLATE_PROFESSIONAL:
            # 专业模板：顶部渐变效果（用多个矩形模拟）
            for i in range(100):
                alpha = int(255 * (1 - i / 100))
                color = (
                    int(colors["primary"][0] * (1 - i / 100) +
                        colors["background"][0] * (i / 100)),
                    int(colors["primary"][1] * (1 - i / 100) +
                        colors["background"][1] * (i / 100)),
                    int(colors["primary"][2] * (1 - i / 100) +
                        colors["background"][2] * (i / 100)),
                )
                LawyerShareCardService._draw_rounded_rectangle(
                    draw,
                    (0, i, LawyerShareCardService.CARD_WIDTH, i + 1),
                    radius=0,
                    fill=color,
                )

        elif template == LawyerShareCardService.TEMPLATE_ELEGANT:
            # 优雅模板：右上角装饰圆
            LawyerShareCardService._draw_rounded_rectangle(
                draw,
                (LawyerShareCardService.CARD_WIDTH -
                 150, 0, LawyerShareCardService.CARD_WIDTH, 150),
                radius=0,
                fill=colors["primary"],
            )
            # 左下角装饰圆
            LawyerShareCardService._draw_rounded_rectangle(
                draw,
                (0, LawyerShareCardService.CARD_HEIGHT - 100,
                 100, LawyerShareCardService.CARD_HEIGHT),
                radius=0,
                fill=colors["accent"],
            )

        # 绘制律师头像占位符（圆形）
        avatar_x = 80
        avatar_y = 80
        avatar_radius = 60
        LawyerShareCardService._draw_rounded_rectangle(
            draw,
            (avatar_x - avatar_radius, avatar_y - avatar_radius,
             avatar_x + avatar_radius, avatar_y + avatar_radius),
            radius=avatar_radius,
            fill=colors["secondary"],
        )

        # 绘制律师姓名
        name = lawyer.name or "律师"
        name_bbox = name_font.getbbox(name)
        name_width = name_bbox[2] - name_bbox[0]
        draw.text((avatar_x + avatar_radius + 30, avatar_y - 20),
                  name, font=name_font, fill=colors["text"])

        # 绘制律师职称
        title = lawyer.title or "执业律师"
        draw.text((avatar_x + avatar_radius + 30, avatar_y + 40),
                  title, font=title_font, fill=colors["secondary"])

        # 绘制评分
        rating = lawyer.rating or 5.0
        rating_text = f"{rating:.1f}分"
        draw.text((avatar_x + avatar_radius + 30, avatar_y + 90),
                  rating_text, font=text_font, fill=colors["accent"])

        # 绘制星星
        star_x = avatar_x + avatar_radius + 30 + 100
        star_y = avatar_y + 90
        for i in range(5):
            star_color = colors["accent"] if i < int(
                rating) else colors["secondary"]
            LawyerShareCardService._draw_star(
                draw, (star_x + i * 25, star_y + 10), 8, star_color)

        # 绘制专长
        specialties = lawyer.specialties or ""
        if specialties:
            specialties_list = [s.strip()
                                for s in specialties.split(",") if s.strip()]
            specialties_text = " | ".join(specialties_list[:3])  # 最多显示3个专长
            draw.text(
                (avatar_x,
                 avatar_y + avatar_radius + 30),
                f"专长：{specialties_text}",
                font=text_font,
                fill=colors["text_light"])

        # 绘制律所名称
        if firm_name:
            draw.text(
                (avatar_x,
                 avatar_y + avatar_radius + 60),
                f"律所：{firm_name}",
                font=text_font,
                fill=colors["text_light"])

        # 绘制经验年限
        experience = lawyer.experience_years or 0
        draw.text(
            (avatar_x,
             avatar_y + avatar_radius + 90),
            f"执业经验：{experience}年",
            font=text_font,
            fill=colors["text_light"])

        # 绘制咨询数量
        case_count = lawyer.case_count or 0
        draw.text(
            (avatar_x + 300,
             avatar_y + avatar_radius + 90),
            f"服务案例：{case_count}件",
            font=text_font,
            fill=colors["text_light"])

        # 绘制评价数量
        review_count = lawyer.review_count or 0
        draw.text(
            (avatar_x + 500,
             avatar_y + avatar_radius + 90),
            f"用户评价：{review_count}条",
            font=text_font,
            fill=colors["text_light"])

        # 绘制底部信息
        if template == LawyerShareCardService.TEMPLATE_SIMPLE:
            # 简洁模板：底部显示二维码占位符
            qr_x = LawyerShareCardService.CARD_WIDTH - 120
            qr_y = LawyerShareCardService.CARD_HEIGHT - 120
            LawyerShareCardService._draw_rounded_rectangle(
                draw,
                (qr_x, qr_y, qr_x + 100, qr_y + 100),
                radius=5,
                fill=colors["background"],
                outline=colors["secondary"],
                width=2,
            )
            draw.text((qr_x + 10, qr_y + 40), "扫码咨询",
                      font=small_font, fill=colors["text_light"])

        elif template == LawyerShareCardService.TEMPLATE_PROFESSIONAL:
            # 专业模板：底部显示联系方式
            contact_y = LawyerShareCardService.CARD_HEIGHT - 50
            draw.text((avatar_x, contact_y), "专业法律服务 · 值得信赖",
                      font=text_font, fill=colors["text_light"])

        elif template == LawyerShareCardService.TEMPLATE_ELEGANT:
            # 优雅模板：底部显示标语
            slogan_y = LawyerShareCardService.CARD_HEIGHT - 50
            draw.text((avatar_x, slogan_y), "用心服务每一位客户",
                      font=text_font, fill=colors["text_light"])

        # 转换为字节
        img_bytes = io.BytesIO()
        img.save(img_bytes, format="PNG")
        img_bytes.seek(0)

        return img_bytes.getvalue()

    @staticmethod
    async def get_card_url(
        db: AsyncSession,
        lawyer_id: int,
        template: Literal["simple", "professional", "elegant"] = "simple",
    ) -> str:
        """
        获取律师分享卡片URL

        Args:
            db: 数据库会话
            lawyer_id: 律师ID
            template: 卡片模板类型

        Returns:
            卡片URL
        """
        # 这里可以集成对象存储服务，将生成的卡片上传到OSS/S3
        # 暂时返回一个模拟URL
        return f"/api/lawyer/{lawyer_id}/share-card?template={template}"
