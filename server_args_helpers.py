import urllib
from enum import Enum, auto
from flask import abort
from Env import Env


class Args(Enum):
    image_id      = auto(),
    mult_image_ids = auto(),
    page          = auto(),
    limit         = auto(),
    tags          = auto(),
    tag_set       = auto(),
    min_rating    = auto(),
    max_rating    = auto(),
    study_timer   = auto(),
    is_same_folder = auto()


def get_arg(args, arg_name:'Args') -> 'int|[int]|str|([str],[str])':
    """
    :param args:
    :param arg_name:
    :return: page argument returned is counted from 0
    """
    match arg_name:
        case Args.page:
            page = int(args.get(Args.page.name, default='1'))
            page = max(page - 1, 0)
            return page

        case Args.limit:
            return int(args.get(Args.limit.name, default=Env.DEFAULT_PER_PAGE_LIMIT))

        case Args.tags:
            return get_tag_names(args)

        case Args.tag_set:
            set_id = args.get('tag-set', default='1')
            return set_id if not set_id is '' else '1'

        case Args.mult_image_ids:
            imgs = args.get('image-id', default="")
            return [int(img) for img in imgs.split(',')]

        case Args.image_id:
            return int(args.get('image-id', default="-1"))

        case Args.min_rating:
            return int(args.get('minr', default='0'))

        case Args.max_rating:
            return int(args.get('maxr', default='9999'))

        case Args.study_timer:
            return int(args.get('timer', default=Env.DEFAULT_STUDY_TIMER))

        case Args.is_same_folder:
            return int(args.get('same-folder', default='0'))
        
        case _:
            abort(404, f'Error: Unknown argument "{arg_name}"')

def get_tag_names(args):
    tags_all = urllib.parse.unquote(args.get(Args.tags.name, default=""), encoding='utf-8', errors='replace').split(',')
    tags_pos = [tag for tag in tags_all if not tag.startswith('-')]
    tags_neg = [tag[1:] for tag in tags_all if tag.startswith('-')]

    # tags_pos = Ctrl.get_tags_by_names(tags_pos)
    # tags_neg = Ctrl.get_tags_by_names(tags_neg)
    return tags_pos, tags_neg

def get_offset_by_page(page:int, limit:int) -> int:
    return limit * page

def get_current_paging(args):
    """
    :param args: Web request args
    :return: page, offset, limit
    """
    limit = get_arg(args, Args.limit)
    page = get_arg(args, Args.page)
    offset = get_offset_by_page(page, limit)
    return page, offset, limit