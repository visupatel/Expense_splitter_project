
def invitation_email(group, admin_name, invitation_link):
    return f"""
    <html>
    <body style="margin:0; padding:0; background:#f4f6f7; font-family:Arial, sans-serif;">

        <div style="max-width:600px; margin:40px auto; background:#ffffff; border-radius:12px; padding:25px; box-shadow:0 2px 10px rgba(0,0,0,0.1);">

            <!-- Header -->
            <h2 style="color:#2f8f89; text-align:center; margin-bottom:20px;">
                You're Invited 🎉
            </h2>

            <!-- Body -->
            <p style="font-size:15px;">
                Hello <b>Dear User</b>,
            </p>

            <p style="font-size:15px; line-height:1.5;">
                <b>{admin_name}</b> has invited you to join the group
                <b style="color:#2f8f89;">{group.name}</b>.
            </p>

            <!-- Info Box -->
            <div style="background:#f1f7f7; padding:15px; border-radius:8px; margin:20px 0;">
                <p style="margin:0;"><b>Group Name:</b> {group.name}</p>
                <p style="margin:5px 0 0;"><b>Admin:</b> {admin_name}</p>
            </div>

            <!-- Button -->
            <div style="text-align:center; margin:30px 0;">
                <a href="{invitation_link}"
                   style="background:#2f8f89; color:white; padding:12px 25px;
                   text-decoration:none; border-radius:6px; font-weight:bold; display:inline-block;">
                    Join Group
                </a>
            </div>

            <p style="font-size:12px; color:gray; text-align:center;">
                If you didn’t expect this invitation, you can ignore this email.
            </p>

        </div>

    </body>
    </html>
    """





def otp_email(user, otp):
    return f"""
    <div style="font-family:Arial; background:#f4f6f7; padding:20px;">

        <div style="max-width:500px; margin:auto; background:#fff; padding:25px; border-radius:10px;">

            <h2 style="color:#2f8f89; text-align:center;">OTP Verification 🔐</h2>

            <p>Hello <b>{user.username}</b>,</p>

            <p>Your OTP for password reset is:</p>

            <div style="font-size:22px; text-align:center; padding:15px;
                        background:#f1f7f7; border-radius:8px; margin:20px 0;">
                <b>{otp}</b>
            </div>

            <p style="color:red;">
                This OTP will expire in 10 minutes. Do not share it with anyone.
            </p>

        </div>
    </div>
    """





def budget_alert_email(group, category, limit, spent):
    return f"""
    <div style="font-family:Arial; background:#f4f6f7; padding:20px;">

        <div style="max-width:550px; margin:auto; background:#fff; padding:25px; border-radius:10px;">

            <h2 style="color:#e74c3c; text-align:center;">Budget Alert ⚠️</h2>

            <p>Hello Group Member,</p>

            <p>Budget limit for <b>{category}</b> has been exceeded in group
            <b>{group.name}</b>.</p>

            <div style="background:#f9ebea; padding:15px; border-radius:8px; margin:20px 0;">
                <p><b>Budget Limit:</b> {limit}</p>
                <p><b>Total Spent:</b> {spent}</p>
            </div>

            <p>Please review your expenses.</p>

        </div>
    </div>
    """