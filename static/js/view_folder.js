import {ApiTags} from "api";
import {WidgetImageTagsFilter} from "image_tools/widget_tags_filter.js"
import {WidgetImageTagsEditor} from "image_tools/widget_tags_editor.js"
import {WidgetBoard}           from "image_tools/widget_board.js"
import {ImageSelection}        from "image_tools/image_selection.js"
import {RateMultImages}        from "image_tools/rating.js"
import {fetchAndSimpleFeedback} from '/static/js/main.js'
import {MutationAttributeObserver} from '/static/js/mut_attr_observer.js'
import {ImageLazyLoad } from '/static/js/image_lazy_load.js'


let tagsFilter = new WidgetImageTagsFilter('', '#tags-filter-btn', true)
let tagsEditor = new WidgetImageTagsEditor('', '#tags-editor-btn', () => selection)
let boardAdd = new WidgetBoard('', '#board-show-btn', () => selection.selectedIds)

let rating = null
let selection = null



// fetch tags button
function fetchTags()
{
    showTagsMode = (showTagsMode + 1) % 2

    // hide shown tags
    if (showTagsMode === 0)
    {
        document.querySelectorAll('.tags-list').forEach(elem => elem.textContent = '')
        document.querySelectorAll('.overlay').forEach(elem => elem.classList.remove('vis-hide'))
    }
    // fetch tags
    else if (showTagsMode === 1)
    {
        // all ids on page
        const allIds = Array.from(document.querySelectorAll('.thumbnail')).map((tile) => parseInt(tile.getAttribute('data-id')))
        ApiTags.GetBulk(allIds)
            .then(data =>
            {
                if (!data) throw new Error('Network response was not ok')
                document.querySelectorAll('.thumbnail').forEach((tile) => {
                    const id = tile.getAttribute('data-id')
                    tile.querySelector('.tags-list').textContent = data[id].join(', ')
                    tile.querySelector('.overlay').classList.remove('vis-hide')
                })
            })
            .catch(error =>
            {
                console.error('There was a problem with the fetch operation:', error)
            });
    }
}

function setFolderCover(e)
{
    if (selection.selectedIds.length !== 1) { return }
    fetchAndSimpleFeedback(`/set-folder-cover?image-id=${selection.selectedIds[0]}`, e.currentTarget)
}

function hideFolder(e)
{
    if (selection.selectedIds.length !== 1) { return }
    fetchAndSimpleFeedback(`/toggle-folder-hide?image-id=${selection.selectedIds[0]}`, e.currentTarget)
}

function folderOrdUp(e)
{
    if (selection.selectedIds.length !== 1) { return }
    fetchAndSimpleFeedback(`/folder-ord-add?image-id=${selection.selectedIds[0]}&rating=1`, e.currentTarget)
}

function folderOrdDown(e)
{
    if (selection.selectedIds.length !== 1) { return }
    fetchAndSimpleFeedback(`/folder-ord-add?image-id=${selection.selectedIds[0]}&rating=-1`, e.currentTarget)
}

document.getElementById('tags-show-btn').addEventListener('click', fetchTags)
// document.getElementById('tags-open-btn').addEventListener('click', toggleTagsPopupDisplay)
// document.getElementById('tags-filter-btn').addEventListener('click', toggleTagsFilterDisplay)

document.getElementById('fld-cover').addEventListener('click', setFolderCover)
document.getElementById('fld_hide').addEventListener('click', hideFolder)
document.getElementById('fld_ord_up').addEventListener('click', folderOrdUp)
document.getElementById('fld_ord_dn').addEventListener('click', folderOrdDown)

document.addEventListener('keydown', function(e)
{
    // select all
    if (selection.selectionMode && e.code === 'KeyA' && e.shiftKey)
    {
        selection.selectAll()
    }
    // show/hide tags
    else if (e.code === 'KeyW')
    {
        fetchTags()
    }
    // toggle selection mode
    else if (e.code === 'KeyS' && !e.shiftKey)
    {
        selection.toggleSelectionMode()
    }
})

// 0 - not showing
// 1 - showing
let showTagsMode = 0

document.addEventListener('DOMContentLoaded', () =>
{
    // reveal on load
    const thumbs = document.querySelectorAll('.thumb')
    thumbs.forEach((elem) =>
    {
        new MutationAttributeObserver(elem, 'src', (target) =>
        {
            target.classList.remove('thumb-hidden')
        })
    })

    new ImageLazyLoad('.thumb', false, '300px')

    rating = new RateMultImages('#rate-up', '#rate-dn', 'loading', 'op-success', 'op-fail')
    rating.updateImageIds = function ()
    {
        this.setImageIds(selection.selectedIds)
    }

    selection = new ImageSelection('toggle-selection-mode-btn', '.gallery', '.thumbnail')

    tagsEditor.showPins()

}, false)