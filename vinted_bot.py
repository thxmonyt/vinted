import discord
from discord import app_commands
import smtplib
import ssl
import asyncio
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import aiohttp
from datetime import datetime

# ─── CONFIG ──────────────────────────────────────────────────────────────────
DISCORD_TOKEN = os.environ.get("DISCORD_TOKEN")
SMTP_USER     = os.environ.get("SMTP_USER")
SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD")
SMTP_HOST     = "send.one.com"
SMTP_PORT     = 587
# ─────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
intents.message_content = True
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)

last_attachments = {}


def build_vinted_html(seller: str, buyer: str, product: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#ffffff;">
<table border="0" width="100%" cellspacing="0" cellpadding="0"
       style="font-family:Helvetica,sans-serif;max-width:680px;margin:0 auto;">
  <tbody>
    <tr>
      <td style="padding:0 25px;height:110px;vertical-align:middle;">
        <a href="https://vinted.nl/" target="_blank">
          <img src="https://static-assets.vinted.com/images/email/_shared/logo/default.png"
               height="30" border="0" alt="Vinted" style="display:block;height:30px;" />
        </a>
      </td>
    </tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>Hello {seller},</b>
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>{buyer}</b> has bought <b>{product}</b>.
      </td>
    </tr>
    <tr><td style="height:27px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        We will transfer the buyer's payment to your Vinted Balance once the order is completed.
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Please send this order within 5 days.<br>Here's what you need to do:
      </td>
    </tr>
    <tr><td style="height:10px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;">
        <ol style="font-family:Helvetica,sans-serif;font-size:16px;color:rgb(51,51,51);line-height:22px;margin:0;padding-left:20px;">
          <li style="margin-bottom:8px;">
            Go to the <a href="https://www.vinted.nl/inbox/17492277494?l=email.body.new_msg.view&login=true&source=email&t=in&type=conversation" style="color:rgb(0,119,130);text-decoration:underline;">message thread</a>
            between you and the buyer to generate your shipping label.
          </li>
          <li style="margin-bottom:8px;">
            Follow the first steps on Vinted, and then the final steps in the email that arrives after your label is created.
          </li>
          <li style="margin-bottom:8px;">
            If you need to print the label and attach it, always make sure there is no tape covering the barcode - even clear tape can get in the way of scanning. You can use your own packaging, or buy a separate envelope or box.
          </li>
        </ol>
      </td>
    </tr>
    <tr><td style="height:27px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        It's also a good idea to get in touch with <b>{buyer}</b> and let them know when you've sent the item.
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Team Vinted
      </td>
    </tr>
    <tr><td style="height:30px;">&nbsp;</td></tr>
    <tr>
      <td style="text-align:right;background:#ffffff;">
        <img src="https://static-assets.vinted.com/admin/editor_assets/en/subtract-footer.png"
             width="680" border="0" style="display:block;max-width:680px;width:100%;" />
      </td>
    </tr>
    <tr>
      <td style="background:rgb(245,246,247);padding:20px 25px;font-family:Helvetica,sans-serif;font-size:12px;line-height:16px;color:rgb(153,153,153);">
        We are required to send you this email in order to fulfill our
        <a href="https://www.vinted.nl/terms_and_conditions" target="_blank" style="color:rgb(51,51,51);text-decoration:underline;">Terms and Conditions</a>,
        or for other legal reasons. It is not possible to unsubscribe from these emails.
        To read up on your rights and more detailed information on how we use your personal data, please see our
        <a href="https://www.vinted.nl/privacy-policy" target="_blank" style="color:rgb(51,51,51);text-decoration:underline;">Privacy Policy</a>.
      </td>
    </tr>
    <tr><td style="background:rgb(245,246,247);height:64px;">&nbsp;</td></tr>
  </tbody>
</table>
</body>
</html>"""


def build_label_html(seller: str, product: str, deadline: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0"></head>
<body style="margin:0;padding:0;background:#ffffff;">
<table border="0" width="100%" cellspacing="0" cellpadding="0"
       style="font-family:Helvetica,sans-serif;max-width:680px;margin:0 auto;">
  <tbody>
    <tr>
      <td style="padding:0 25px;height:110px;vertical-align:middle;">
        <a href="https://vinted.nl/" target="_blank">
          <img src="https://static-assets.vinted.com/images/email/_shared/logo/default.png"
               height="30" border="0" alt="Vinted" style="display:block;height:30px;" />
        </a>
      </td>
    </tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>Hello {seller},</b>
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Your shipping label is <i>attached</i> to this message.
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>Shipment&nbsp;Information</b>
      </td>
    </tr>
    <tr><td style="height:8px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;">
        <table border="0" cellspacing="0" cellpadding="4" align="left"
               style="border-collapse:collapse;border:0;width:100%;margin-bottom:20px;font-family:Helvetica,sans-serif;font-size:16px;color:rgb(51,51,51);">
          <tbody>
            <tr>
              <td style="border:0;width:160px;padding:4px 8px 4px 0;font-family:Helvetica,sans-serif;vertical-align:top;"><b>Item name:</b></td>
              <td style="border:0;padding:4px 0;font-family:Helvetica,sans-serif;vertical-align:top;">{product}</td>
            </tr>
            <tr>
              <td style="border:0;padding:4px 8px 4px 0;font-family:Helvetica,sans-serif;vertical-align:top;"><b>Package size:</b></td>
              <td style="border:0;padding:4px 0;font-family:Helvetica,sans-serif;vertical-align:top;">Under 2000.0 g</td>
            </tr>
            <tr>
              <td style="border:0;padding:4px 8px 4px 0;font-family:Helvetica,sans-serif;vertical-align:top;"><b>Shipment deadline:</b></td>
              <td style="border:0;padding:4px 0;font-family:Helvetica,sans-serif;vertical-align:top;">{deadline} 11:56 AM</td>
            </tr>
            <tr>
              <td style="border:0;padding:4px 8px 4px 0;font-family:Helvetica,sans-serif;vertical-align:top;"><b>Transaction ID:</b></td>
              <td style="border:0;padding:4px 0;font-family:Helvetica,sans-serif;vertical-align:top;">14921055404</td>
            </tr>
          </tbody>
        </table>
      </td>
    </tr>
    <tr><td style="height:20px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>Here are the next steps to complete this transaction:</b><br><br>
        <b>Pack your item(s)</b><br>
        Use <a href="https://www.vinted.fr/help/65" style="color:rgb(0,119,130);text-decoration:underline;">packaging</a> that's sturdy enough to protect the item(s) you're sending.<br>
        The dimensions of your parcel should not exceed 80 cm x 50 cm x 35 cm, max weight - 2000 g.<br><br>
        <b>Bring the parcel to the drop-off point</b><br>
        Check the nearest DHL ServicePoint <a href="https://parcelshopfinder.dhlparcel.com/?countryCode=nl" style="color:rgb(0,119,130);text-decoration:underline;">drop-off point</a> for the opening hours.
        You can drop-off parcel at Servicepoint parcel shop. Keep the proof of shipping for any inquiries.<br><br>
        <b>Show the digital label on your phone (there's no need to print it)</b><br>
        Staff at the drop-off point will scan the code, then print the label and attach it to the parcel for you.<br><br>
        <b>Track your parcel's journey</b><br>
        After drop-off, both the seller and the buyer can track the parcel via the conversation screen. Allow up to 48 hours for the information to appear on Vinted.<br><br>
        <b>IMPORTANT: Ship your parcel before {deadline} 11:56 AM to avoid the transaction being cancelled.</b>
      </td>
    </tr>
    <tr><td style="height:18px;">&nbsp;</td></tr>
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Team Vinted
      </td>
    </tr>
    <tr><td style="height:30px;">&nbsp;</td></tr>
    <tr>
      <td style="text-align:right;background:#ffffff;">
        <img src="https://static-assets.vinted.com/admin/editor_assets/en/subtract-footer.png"
             width="680" border="0" style="display:block;max-width:680px;width:100%;" />
      </td>
    </tr>
    <tr>
      <td style="background:rgb(245,246,247);padding:20px 25px;font-family:Helvetica,sans-serif;font-size:12px;line-height:16px;color:rgb(153,153,153);">
        We are required to send you this email in order to fulfill our
        <a href="https://www.vinted.nl/terms_and_conditions" target="_blank" style="color:rgb(51,51,51);text-decoration:underline;">Terms and Conditions</a>,
        or for other legal reasons. It is not possible to unsubscribe from these emails.
        To read up on your rights and more detailed information on how we use your personal data, please see our
        <a href="https://www.vinted.nl/privacy-policy" target="_blank" style="color:rgb(51,51,51);text-decoration:underline;">Privacy Policy</a>.
      </td>
    </tr>
    <tr><td style="background:rgb(245,246,247);height:64px;">&nbsp;</td></tr>
  </tbody>
</table>
</body>
</html>"""


def send_sync(to_address, subject, html, attachment_data=None, attachment_name=None):
    msg = MIMEMultipart("mixed")
    msg["Subject"] = subject
    msg["From"]    = f"Team Vinted <{SMTP_USER}>"
    msg["To"]      = to_address
    alt = MIMEMultipart("alternative")
    alt.attach(MIMEText(html, "html", "utf-8"))
    msg.attach(alt)
    if attachment_data and attachment_name:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(attachment_data)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f'attachment; filename="{attachment_name}"')
        msg.attach(part)
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls(context=ssl.create_default_context())
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_address, msg.as_string())


async def send_email(to_address, subject, html, attachment_data=None, attachment_name=None):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, send_sync, to_address, subject, html, attachment_data, attachment_name)


class VintedModal(discord.ui.Modal, title="Vinted Mail Versturen"):
    seller          = discord.ui.TextInput(label="Naam verkoper (ontvanger)", placeholder="bijv. wlucien90", required=True, max_length=100)
    buyer           = discord.ui.TextInput(label="Naam koper", placeholder="bijv. sandravangaal", required=True, max_length=100)
    product         = discord.ui.TextInput(label="Productnaam", placeholder="bijv. Samsung Galaxy S23 Ultra", required=True, max_length=200)
    recipient_email = discord.ui.TextInput(label="E-mailadres ontvanger", placeholder="bijv. verkoper@hotmail.com", required=True, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        try:
            html = build_vinted_html(self.seller.value.strip(), self.buyer.value.strip(), self.product.value.strip())
            await send_email(self.recipient_email.value.strip(), "You've sold an item on Vinted", html)
            embed = discord.Embed(title="✅ Mail verstuurd!", color=0x007782)
            embed.add_field(name="Naar",     value=self.recipient_email.value.strip(), inline=False)
            embed.add_field(name="Verkoper", value=self.seller.value.strip(),          inline=True)
            embed.add_field(name="Koper",    value=self.buyer.value.strip(),           inline=True)
            embed.add_field(name="Product",  value=self.product.value.strip(),         inline=False)
            embed.set_footer(text="Verstuurd via noreply@vinted-service.nl")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Fout:\n```{e}```", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ Onverwachte fout.", ephemeral=True)


class LabelModal(discord.ui.Modal, title="Shipping Label Versturen"):
    seller          = discord.ui.TextInput(label="Naam verkoper (ontvanger)", placeholder="bijv. norae880", required=True, max_length=100)
    product         = discord.ui.TextInput(label="Productnaam", placeholder="bijv. Canon powershot SX740HS", required=True, max_length=200)
    deadline        = discord.ui.TextInput(label="Deadline datum (DD/MM/YYYY)", placeholder="bijv. 29/04/2026", required=True, max_length=20)
    recipient_email = discord.ui.TextInput(label="E-mailadres ontvanger", placeholder="bijv. verkoper@hotmail.com", required=True, max_length=200)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)
        seller_val   = self.seller.value.strip()
        product_val  = self.product.value.strip()
        deadline_val = self.deadline.value.strip()
        email_val    = self.recipient_email.value.strip()
        subject      = f"{product_val} shipping label – use by {deadline_val} 11:56 AM"

        attachment_data = None
        attachment_name = None
        if interaction.channel_id in last_attachments:
            att_url, att_name = last_attachments[interaction.channel_id]
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(att_url) as resp:
                        if resp.status == 200:
                            attachment_data = await resp.read()
                            attachment_name = att_name
            except Exception:
                pass

        try:
            html = build_label_html(seller_val, product_val, deadline_val)
            await send_email(email_val, subject, html, attachment_data, attachment_name)
            embed = discord.Embed(title="✅ Label mail verstuurd!", color=0x007782)
            embed.add_field(name="Naar",     value=email_val,                  inline=False)
            embed.add_field(name="Verkoper", value=seller_val,                 inline=True)
            embed.add_field(name="Product",  value=product_val,                inline=False)
            embed.add_field(name="Deadline", value=f"{deadline_val} 11:56 AM", inline=True)
            embed.add_field(name="Bijlage",  value=f"✅ {attachment_name}" if attachment_name else "⚠️ Geen foto gevonden", inline=False)
            embed.set_footer(text="Verstuurd via noreply@vinted-service.nl")
            await interaction.followup.send(embed=embed, ephemeral=True)
        except Exception as e:
            await interaction.followup.send(f"❌ Fout:\n```{e}```", ephemeral=True)

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message("❌ Onverwachte fout.", ephemeral=True)


@tree.command(name="vinted", description="Stuur een Vinted verkoopbevestiging")
async def vinted_command(interaction: discord.Interaction):
    await interaction.response.send_modal(VintedModal())


@tree.command(name="label", description="Stuur een verzendlabel mail (stuur eerst de foto in chat)")
async def label_command(interaction: discord.Interaction):
    await interaction.response.send_modal(LabelModal())


@client.event
async def on_message(message: discord.Message):
    if message.author == client.user:
        return
    if message.attachments:
        for att in message.attachments:
            if any(att.filename.lower().endswith(ext) for ext in [".png", ".jpg", ".jpeg", ".pdf", ".gif", ".webp"]):
                last_attachments[message.channel.id] = (att.url, att.filename)


@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online als {client.user} — /vinted en /label actief")


client.run(DISCORD_TOKEN)
