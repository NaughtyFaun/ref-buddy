from flask import Flask, render_template_string, request, send_file, abort, send_from_directory, render_template

from image_metadata_controller import ImageMetadataController as ImageMetadataCtrl
from image_metadata_overview import ImageMetadataOverview, OverviewPath
import os
from datetime import datetime
from Env import Env
from models.models_lump import Session
from server_args_helpers import get_arg, get_current_paging, Args
from server_ext_dupes import routes_dupes
from server_ext_rating import routes_rating
from server_ext_tags import routes_tags
from server_widget_helpers import get_paging_widget, get_tags_editor

app = Flask(__name__, static_url_path='/static')
app.config['THUMB_STATIC'] = Env.THUMB_PATH

app.register_blueprint(routes_rating)
app.register_blueprint(routes_tags)
app.register_blueprint(routes_dupes)

@app.route('/')
def index():
    images = ImageMetadataOverview.get_overview()
    return render_template('tpl_index.html', images=images)

@app.route('/favs')
def view_favs():
    page, offset, limit = get_current_paging(request.args)
    rating = get_arg(request.args, Args.min_rating)
    tags_pos, tags_neg = get_arg(request.args, Args.tags)

    tags_pos = ImageMetadataCtrl.get_tags_by_names(tags_pos)
    tags_neg = ImageMetadataCtrl.get_tags_by_names(tags_neg)

    images = ImageMetadataCtrl.get_favs(start=offset, count=limit, tags=(tags_pos,tags_neg), min_rating=rating)

    paging = get_paging_widget(page)
    tags_editor = get_tags_editor()

    return render_template('tpl_view_folder.html', title='Favorites', paging=paging, images=images, overview=None, tags_editor=tags_editor)

@app.route('/latest_study')
def view_last():
    page, offset, limit = get_current_paging(request.args)
    rating = get_arg(request.args, Args.min_rating)

    tags_pos, tags_neg = get_arg(request.args, Args.tags)

    tags_pos = ImageMetadataCtrl.get_tags_by_names(tags_pos)
    tags_neg = ImageMetadataCtrl.get_tags_by_names(tags_neg)

    images = ImageMetadataCtrl.get_last(start=offset, count=limit, tags=(tags_pos,tags_neg), min_rating=rating)

    paging = get_paging_widget(page)
    tags_editor = get_tags_editor()

    return render_template('tpl_view_folder.html', title='Latest study', paging=paging, images=images, overview=None, tags_editor=tags_editor)

@app.route('/folder/<int:path_id>')
def view_folder(path_id):
    rating = get_arg(request.args, Args.min_rating)
    tags_pos, tags_neg = get_arg(request.args, Args.tags)

    session = Session()
    tags_pos = ImageMetadataCtrl.get_tags_by_names(tags_pos, session=session)
    tags_neg = ImageMetadataCtrl.get_tags_by_names(tags_neg, session=session)

    study_type, path, images = ImageMetadataCtrl.get_all_by_path_id(path_id, tags=(tags_pos,tags_neg), min_rating=rating, session=session)
    overview = OverviewPath.from_image_metadata(images[0])


    tags_editor = get_tags_editor(session=session)

    out = render_template('tpl_view_folder.html', title='Folder', images=images, overview=overview, tags_editor=tags_editor)
    session.close()
    return out

@app.route('/thumb/<path:path>')
def send_static_thumb(path):
    return send_from_directory(app.config['THUMB_STATIC'], path)

@app.route('/image/<int:image_id>')
def serve_image(image_id):
    metadata = ImageMetadataCtrl.get_by_id(image_id)
    ext = os.path.splitext(metadata.path)[1]
    return send_file(os.path.join(Env.IMAGES_PATH, metadata.path), mimetype=f'image/{ext}')

@app.route('/study-image/<int:image_id>')
def study_image(image_id):
    timer = get_arg(request.args, Args.study_timer)

    session = Session()
    metadata = ImageMetadataCtrl.get_by_id(image_id, session=session)
    study_types = ImageMetadataCtrl.get_study_types()
    if metadata is None:
        abort(404, f'Error: No images found with id "{image_id}"')

    out = render_template('tpl_image.html', image=metadata, timer=timer, study_types=study_types, tags=[t.tag for t in metadata.tags])
    session.close()
    return out

@app.route('/study-random')
def study_random():
    study_type    = int(request.args.get('study-type', default='1'))
    same_folder   = get_arg(request.args, Args.is_same_folder)
    prev_image_id = get_arg(request.args, Args.image_id)
    rating        = get_arg(request.args, Args.min_rating)
    timer         = get_arg(request.args, Args.study_timer)
    tags_pos, tags_neg = get_arg(request.args, Args.tags)

    session = Session()

    tags_pos = ImageMetadataCtrl.get_tags_by_names(tags_pos, session=session)
    tags_neg = ImageMetadataCtrl.get_tags_by_names(tags_neg, session=session)

    study_types = ImageMetadataCtrl.get_study_types(session=session)
    metadata = ImageMetadataCtrl.get_random_by_study_type(study_type, same_folder, prev_image_id, min_rating=rating, tags=(tags_pos, tags_neg), session=session)
    if metadata is None:
        return f'Error: No images found"'

    out = render_template('tpl_image.html', image=metadata, timer=timer, study_types=study_types, tags=[t.tag for t in metadata.tags])

    session.close()
    return out

@app.route('/set-image-fav')
def set_image_fav():
    args = request.args
    is_fav = int(args.get('is-fav'))
    image_id = get_arg(request.args, Args.image_id)

    r = ImageMetadataCtrl.set_image_fav(image_id, is_fav)
    if not r:
        abort(404, 'Something went wrong, fav not set, probably...')
    return render_template_string('yep')

@app.route('/set-image-last-viewed')
def set_image_last_viewed():
    image_id = get_arg(request.args, Args.image_id)
    now = datetime.now()

    r = ImageMetadataCtrl.set_image_last_viewed(image_id, now)

    if not r:
        abort(404, 'Something went wrong, last viewed not updated, probably...')
    return render_template_string('yep')


if __name__ == '__main__':
    # db = sqlite3.connect(Env.DB_FILE)
    # ImageMetadataCtrl.static_initialize(db)

    app.run(host='0.0.0.0', port=Env.SERVER_PORT)
