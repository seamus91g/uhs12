from flask import render_template, url_for, flash, redirect
from flask_login import current_user, login_required
from uhs12app import db
from uhs12app.main.forms import (
    NewShamePostForm,
)
from uhs12app.models import ShamePost
from flask import Blueprint
from uhs12app.users.utils import save_picture

main = Blueprint('main', __name__)

@main.route("/wallofshame", methods=["GET", "POST"])
@login_required
def wallofshame():
    # TODO Tally disapprovals and apply them when user leaves the page
    shame_form = NewShamePostForm()
    if shame_form.validate_on_submit():
        pic_name = save_picture(shame_form.picture.data, sub_dir="wos_pics", output_size=(1024, 1024))
        shame_post = ShamePost(
            houseId=current_user.houseId,
            userId=current_user.id,
            postImage=pic_name,
        )
        db.session.add(shame_post)
        db.session.commit()
        flash(f"Hooray! You have cast shame!", "success")
        return redirect(url_for("main.wallofshame"))
    
    shame_posts = ShamePost.query.order_by(ShamePost.dateCreated.desc()).filter_by(houseId=current_user.houseId).all()

    return render_template("wallofshame.html", shame_posts=shame_posts, form=shame_form)
