"""邮件模板

提供各类邮件的 HTML 和纯文本模板
"""

# ============================================================================
# 密码重置邮件模板
# ============================================================================

PASSWORD_RESET_TEXT_TEMPLATE = """
您好，

您正在重置百姓法律助手账号的密码。

请点击以下链接重置密码（1小时内有效）：
{reset_url}

如果您没有请求重置密码，请忽略此邮件。

百姓法律助手团队
"""

PASSWORD_RESET_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f59e0b, #ea580c); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ color: white; margin: 0; }}
        .content {{ background: #1a1625; color: #e5e5e5; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #f59e0b, #ea580c); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ 百姓法律助手</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p>您正在重置百姓法律助手账号的密码。</p>
            <p style="text-align: center;">
                <a href="{reset_url}" class="button">重置密码</a>
            </p>
            <p>此链接将在 <strong>1小时</strong> 后失效。</p>
            <p>如果您没有请求重置密码，请忽略此邮件。</p>
            <p class="footer">© 百姓法律助手团队</p>
        </div>
    </div>
</body>
</html>
"""

# ============================================================================
# 邮箱验证邮件模板
# ============================================================================

EMAIL_VERIFICATION_TEXT_TEMPLATE = """
您好，

请点击以下链接完成邮箱验证（24小时内有效）：
{verify_url}

如果您没有发起该操作，请忽略此邮件。

百姓法律助手团队
"""

EMAIL_VERIFICATION_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: linear-gradient(135deg, #f59e0b, #ea580c); padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
        .header h1 {{ color: white; margin: 0; }}
        .content {{ background: #1a1625; color: #e5e5e5; padding: 30px; border-radius: 0 0 10px 10px; }}
        .button {{ display: inline-block; background: linear-gradient(135deg, #f59e0b, #ea580c); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; margin: 20px 0; }}
        .footer {{ text-align: center; color: #888; font-size: 12px; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>⚖️ 百姓法律助手</h1>
        </div>
        <div class="content">
            <p>您好，</p>
            <p>请点击以下按钮完成邮箱验证（<strong>24小时</strong>内有效）：</p>
            <p style="text-align: center;">
                <a href="{verify_url}" class="button">验证邮箱</a>
            </p>
            <p>如果您没有发起该操作，请忽略此邮件。</p>
            <p class="footer">© 百姓法律助手团队</p>
        </div>
    </div>
</body>
</html>
"""


def get_password_reset_text_template(reset_url: str) -> str:
    """获取密码重置纯文本模板"""
    return PASSWORD_RESET_TEXT_TEMPLATE.format(reset_url=reset_url)


def get_password_reset_html_template(reset_url: str) -> str:
    """获取密码重置 HTML 模板"""
    return PASSWORD_RESET_HTML_TEMPLATE.format(reset_url=reset_url)


def get_email_verification_text_template(verify_url: str) -> str:
    """获取邮箱验证纯文本模板"""
    return EMAIL_VERIFICATION_TEXT_TEMPLATE.format(verify_url=verify_url)


def get_email_verification_html_template(verify_url: str) -> str:
    """获取邮箱验证 HTML 模板"""
    return EMAIL_VERIFICATION_HTML_TEMPLATE.format(verify_url=verify_url)
