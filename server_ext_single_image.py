import os
from datetime import datetime

from PIL import Image
from flask import render_template_string, request, send_file, abort, render_template, Blueprint, send_from_directory, \
    current_app
from image_metadata_controller import ImageMetadataController as Ctrl
from Env import Env
from models.models_lump import Session, ImageMetadata, Color, ImageColor
from server_args_helpers import get_arg, Args

routes_image = Blueprint('routes_image', __name__)

@routes_image.route('/image/<int:image_id>')
def send_static_image(image_id):
    metadata = Ctrl.get_by_id(image_id)
    ext = os.path.splitext(metadata.path)[1]
    return send_file(os.path.join(Env.IMAGES_PATH, metadata.path), mimetype=f'image/{ext}')

@routes_image.route('/study-image/<int:image_id>')
def study_image(image_id):
    timer = get_arg(request.args, Args.study_timer)

    session = Session()
    metadata = Ctrl.get_by_id(image_id, session=session)
    study_types = Ctrl.get_study_types()
    if metadata is None:
        abort(404, f'Error: No images found with id "{image_id}"')

    out = render_template('tpl_image.html', image=metadata, timer=timer, study_types=study_types, tags=[t.tag for t in metadata.tags])
    session.close()
    return out

@routes_image.route('/study-random')
def study_random():
    # study_type    = int(request.args.get('study-type', default='1'))
    same_folder   = get_arg(request.args, Args.is_same_folder)
    prev_image_id = get_arg(request.args, Args.image_id)
    rating        = get_arg(request.args, Args.min_rating)
    timer         = get_arg(request.args, Args.study_timer)
    tags_pos, tags_neg = get_arg(request.args, Args.tags)
    tag_set_id = get_arg(request.args, Args.tag_set)

    session = Session()
    tags_pos, tags_neg = Ctrl.get_tags_by_set(tag_set_id, tags_pos, tags_neg, session=session)

    study_types = Ctrl.get_study_types(session=session)
    metadata = Ctrl.get_random_by_study_type(0, same_folder, prev_image_id, min_rating=rating, tags=(tags_pos, tags_neg), session=session)
    if metadata is None:
        return f'Error: No images found"'

    out = render_template('tpl_image.html', image=metadata, timer=timer, study_types=study_types, tags=[t.tag for t in metadata.tags])

    session.close()
    return out

@routes_image.route('/set-image-fav')
def set_image_fav():
    args = request.args
    is_fav = int(args.get('is-fav'))
    image_id = get_arg(request.args, Args.image_id)

    r = Ctrl.set_image_fav(image_id, is_fav)
    if not r:
        abort(404, 'Something went wrong, fav not set, probably...')
    return render_template_string('yep')

@routes_image.route('/set-image-last-viewed')
def set_image_last_viewed():
    image_id = get_arg(request.args, Args.image_id)
    now = datetime.now()

    r = Ctrl.set_image_last_viewed(image_id, now)

    if not r:
        abort(404, 'Something went wrong, last viewed not updated, probably...')
    return render_template_string('yep')

@routes_image.route('/thumb/<path:path>')
def send_static_image_thumb(path):
    return send_from_directory(current_app.config['THUMB_STATIC'], path)

@routes_image.route('/color-at-coord')
def get_color_at_coord():
    image_id = get_arg(request.args, Args.image_id)
    x_r = float(request.args.get('x'))
    y_r = float(request.args.get('y'))

    session = Session()
    im = session.get(ImageMetadata, image_id)

    hex_color = '#000000'
    with Image.open(im.path_abs) as image:
        width, height = image.size
        x = int(x_r * width)
        y = int(y_r * height)

        # Calculate the average color of the surrounding pixels
        surrounding_pixels = []
        for i in range(x - 1, x + 2):
            for j in range(y - 1, y + 2):
                pixel = image.getpixel((i, j))
                surrounding_pixels.append(pixel)
        avg_color = tuple(int(sum(channel) / len(channel)) for channel in zip(*surrounding_pixels))

        avg_color = avg_color[:3]
        # Convert the average color to hex
        hex_color = '#%02x%02x%02x' % avg_color

    return render_template_string(hex_color)

@routes_image.route('/save-image-color')
def save_image_color():
    try:
        image_id = get_arg(request.args, Args.image_id)
        x = float(request.args.get('x'))
        y = float(request.args.get('y'))
        hex_color = '#' + request.args.get('hex')
        if hex_color == '#':
            raise ValueError
    except ValueError:
        abort(404, 'Some arguments are missing...')
        return

    print(f'{image_id} {x} {y} {hex_color}')
    session = Session()

    color = session.query(Color).filter(Color.hex == hex_color).first()
    if color is None:
        color = Color(hex=hex_color, color_name=f'image {image_id}')
        session.add(color)
        session.flush()

    session.merge(ImageColor(image_id=image_id, color_id=color.id, x=x, y=y))
    session.commit()

    # color = session.query(Color, )
    return render_template_string('ok')