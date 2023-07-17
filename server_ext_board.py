from flask import Blueprint, request, abort, render_template_string, render_template
from models.models_lump import Session, ImageMetadata, Path, BoardImage, Board
from server_args_helpers import get_arg, Args
from server_widget_helpers import get_boards_all

routes_board = Blueprint('routes_board', __name__)

@routes_board.route('/boards')
def view_board_all():
    session = Session()

    boards = session.query(Board).all()
    out = render_template('tpl_view_board_all.html', boards=boards)
    session.close()
    return out

@routes_board.route('/board/<int:b_id>')
def view_board(b_id):
    session = Session()

    board = session.get(Board, b_id)
    out = render_template('tpl_view_board.html', board=board)
    session.close()
    return out

@routes_board.route('/board-images/<int:b_id>')
def get_board_images(b_id):
    session = Session()

    images = [(bim.image, bim.tr) for bim in session.query(BoardImage).filter(BoardImage.board_id == b_id)]
    json_images = []
    for im, tr in images:
        json_tr = tr\
            .replace('tx', '"tx"')\
            .replace('ty', '"ty"')\
            .replace('rx', '"rx"')\
            .replace('ry', '"ry"')\
            .replace('s', '"s"')
        json = '{' + f'"image_id":{im.image_id},"path":"/thumb/{im.image_id}.jpg","tr":{json_tr}' + '}'
        json_images.append(json)

    str_json = ",".join(json_images)
    out = render_template_string('{' + f'"images":[{str_json}]' + '}')
    session.close()
    return out

@routes_board.route('/set-board-image-transform')
def set_board_image_transform():
    args = request.args
    image_id = get_arg(request.args, Args.image_id)
    b_id = int(args.get('b-id', default='-1'))
    transform = args.get('tr', default='')

    if transform == '' or b_id == -1 or image_id == -1:
        abort(404, 'No transform provided')

    session = Session()
    im = session.query(BoardImage).filter(BoardImage.image_id == image_id, BoardImage.board_id == b_id).first()
    if im is None:
        abort(404, f'Image "{image_id}" is not on board "{b_id}"')

    im.tr = transform.replace('"', '')
    session.commit()
    session.close()
    return 'ok'

@routes_board.route('/board/add-images')
def add_images_to_board():
    image_ids = get_arg(request.args, Args.mult_image_ids)
    b_id = int(request.args.get('b-id', default='-1'))

    if len(image_ids) == 0 or b_id == -1:
        abort(404, "Something went wrong")

    session = Session()
    for im in image_ids:
        session.merge(BoardImage(image_id=im, board_id=b_id))

    session.commit()
    session.close()
    return 'ok'

@routes_board.route('/board/del-images')
def remove_images_from_board():
    image_ids = get_arg(request.args, Args.mult_image_ids)
    b_id = int(request.args.get('b-id', default='-1'))

    if len(image_ids) == 0 or b_id == -1:
        abort(404, "Something went wrong")

    session = Session()
    [session.delete(bim) for bim in session.query(BoardImage).filter(BoardImage.board_id == b_id, BoardImage.image_id.in_(image_ids))]
    session.commit()
    session.close()

    return 'ok'

@routes_board.route('/widget/get-boards-all')
def widget_get_boards_all():
    session = Session()
    out = get_boards_all(session=session)
    session.close()
    return out