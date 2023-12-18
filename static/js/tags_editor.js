class TagItem
{
    _evtTagClick = 'tag_click'
    _evtPinClick = 'tag_pin_click'

    _selCheckbox = 'input[type="checkbox"]'
    _selLabel = 'label'
    _selPin = 'button.tag-pin'

    _container
    _checkbox
    _pin

    _tagId

    _pinned = false

    constructor(containerNode)
    {
        this._container = containerNode
        this._checkbox = this._container.querySelector(this._selCheckbox)
        this._pin = this._container.querySelector(this._selPin)

        this._tagId = this._container.getAttribute('data-id')

        this._itemClickEvent = new CustomEvent(this._evtTagClick, { detail: { tagId: this._tagId }});
        this._pinClickEvent = new CustomEvent(this._evtPinClick,  { detail: { tagId: this._tagId }});

        this._container.querySelector(this._selCheckbox).addEventListener('click', e => { this.tagToggle(e) })
        this._container.querySelector(this._selLabel).addEventListener('click', e => { this.tagToggle(e) })
        this._container.querySelector(this._selPin).addEventListener('click', e => { this.pinToggle(e) })
    }

    tagToggle(e)
    {
        if (e.currentTarget !== this._checkbox)
        {
            e.preventDefault()
        }

        // console.log('TagItem method toggle tag ' + this._container.getAttribute('data-id'))

        // handle input checkbox so it can trigger callbacks too
        if (e.currentTarget === this._checkbox)
        {
            this._checkbox.checked = !this._checkbox.checked
        }

        this.checked = !this.checked
    }

    pinToggle(e)
    {
        e.preventDefault()

        console.log('TagItem method toggle pin ' + this._container.getAttribute('data-id'))
        this.pinned = !this.pinned
    }

    get checked()
    {
        return this._checkbox.checked
    }

    set checked(value)
    {
        if (value === this._checkbox.checked) { return }

        if (value) { this._container.classList.add('tag-selected') }
        else { this._container.classList.remove('tag-selected') }

        this._checkbox.checked = value

        document.dispatchEvent(this._itemClickEvent)
    }

    get pinned()
    {
        return this._pinned
    }

    set pinned(value)
    {
        if (value === this._pinned) { return }

        if (value) { this._pin.classList.add('tag-pin-on') }
        else { this._pin.classList.remove('tag-pin-on') }

        this._pinned = value

        console.log('pinned ' + this._pinned)
        document.dispatchEvent(this._pinClickEvent)
    }

    get color()
    {
        this._container.getAttribute('data-color')
    }
}


// init pins list
const PINS = 'pins_list'
let pinsList = [];
const storedList = localStorage.getItem(PINS)
if (storedList) { pinsList = JSON.parse(storedList) }

// list of all TAG buttons
const tagBtns = {}
// list of all TAG PROXY buttons
const tagProxyBtns = {}
const tmpTagProxyBtns = {}

document.querySelectorAll('.tag-item').forEach(item =>
{
    const tagId = item.getAttribute('data-id')
    tagBtns[tagId] = new TagItem(item)
})

// tags background
document.querySelector('.tags-popup-background').addEventListener('click', closeTagsPopup)


function toggleTagsPopupDisplay()
{
    const popup = document.getElementById('tags-popup')
    if (popup.classList.contains('vis-hide'))
    {
        document.getElementById('tags-popup').classList.remove('vis-hide')
        document.querySelector('.tags-popup-background').style.display = 'block'
        document.getElementById('images-count').textContent = '' + selection.selectedIds.length
    }
    else
    {
        closeTagsPopup()
    }
}

function toggleTagsPinsDisplay()
{
    const popup = document.getElementById('tags-pins')
    popup.classList.toggle('tags-pins-hide')
}

function closeTagsPopup()
{
    document.getElementById('tags-popup').classList.add('vis-hide')
    document.querySelector('.tags-popup-background').style.display = 'none'

    document.getElementById('tags-submit-add').classList.remove('op-success', 'op-fail', 'loading')
    document.getElementById('tags-submit-del').classList.remove('op-success', 'op-fail', 'loading')
    document.getElementById('tags-pins-submit-add').classList.remove('op-success', 'op-fail', 'loading')
    document.getElementById('tags-pins-submit-del').classList.remove('op-success', 'op-fail', 'loading')
}

function clearTagsPopup()
{
    Array.from(document.querySelectorAll('#tags-pins input[type="checkbox"]:checked'))
        .map((checkbox) => { checkbox.checked = false; checkbox.parentNode.classList.remove('tag-selected') })

    Array.from(Object.values(tagBtns)).forEach(t => t.checked = false)
}

function submitAddTags(evt)
{

    if (!selection.selectionMode) { return }

    const elem = evt.currentTarget
    const selectedTags = Array.from(document.querySelectorAll('#tagList input[type="checkbox"]:checked'))
        .map((checkbox) => checkbox.value)

    const idsStr = selection.selectedIds.join(',')
    const tagsStr = selectedTags.join(',')

    elem.classList.add('loading')
    elem.classList.remove('op-success', 'op-fail')

    fetch(`/add-image-tags?image-id=${idsStr}&tags=${tagsStr}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok')
            elem.classList.add('op-success')
            showNewTags(selection.selectedIds, selectedTags, [])
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error)
            elem.classList.add('op-fail')
        })
        .finally(() =>
        {
            elem.classList.remove('loading')
        })
}

function submitRemoveTags(evt)
{
    if (!selection.selectionMode) { return }

    const elem = evt.currentTarget
    const selectedTags = Array.from(document.querySelectorAll('#tagList input[type="checkbox"]:checked'))
        .map((checkbox) => checkbox.value)

    const idsStr = selection.selectedIds.join(',')
    const tagsStr = selectedTags.map(t => '-' + t).join(',')

    elem.classList.add('loading')
    elem.classList.remove('op-success', 'op-fail')

    fetch(`/remove-image-tags?image-id=${idsStr}&tags=${tagsStr}`)
        .then(response => {
            if (!response.ok) throw new Error('Network response was not ok')
            elem.classList.add('op-success')
            showNewTags(selection.selectedIds, [], selectedTags)
        })
        .catch(error => {
            console.error('There was a problem with the fetch operation:', error)
            elem.classList.add('op-fail')
        })
        .finally(() =>
        {
            elem.classList.remove('loading')
        })
}

// show tags in overlay
function showNewTags(ids, ptags = [], ntags = [])
{
    document.querySelectorAll('.thumbnail').forEach(elem =>
    {
        const id = elem.getAttribute('data-id')
        if (!ids.includes(id)) { return }

        elem.querySelector('.overlay').classList.remove('vis-hide')

        const tl = elem.querySelector('.tags-list')
        if (ptags.length > 0)
        {
            let tmp = tl.textContent === '' ? [] : tl.textContent.split(', ')
            tmp = Array.from(new Set([].concat(tmp, ptags)))
            tmp.sort()
            elem.querySelector('.tags-list').textContent = tmp.join(', ')
        }
        if (ntags.length > 0)
        {
            let tmp = tl.textContent === '' ? [] : tl.textContent.split(', ')
            tmp = Array.from(tmp).filter(t => !ntags.includes(t))
            tmp.sort()
            elem.querySelector('.tags-list').textContent = tmp.join(', ')
        }
    })
}

function addTagToPinList(tagId, container, isTmp = false)
{
    if (tagId === '' || tagId === null || !tagBtns.hasOwnProperty(tagId)) { return }

    const tpl = document.getElementById('tag-pin-template')

    let btn = tpl.cloneNode(true)
    container.appendChild(btn)

    const inpt = btn.querySelector('input')
    const label = btn.querySelector('label')

    btn.id = ''
    btn.setAttribute('data-id', tagId)
    inpt.id = 'pin-' + tagId
    inpt.value = tagId
    label.setAttribute('for', 'pin-' + tagId)
    label.textContent = tagId
    label.style.color = tagBtns[tagId].color

    btn.addEventListener('click', evt =>
    {
        evt.preventDefault()

        const proxyItem = evt.currentTarget.querySelector('input')
        console.log(`proxy ${proxyItem}`)
        console.log(proxyItem)
        proxyItem.checked = !proxyItem.checked

        const id = evt.currentTarget.getAttribute('data-id')
        const tag = tagBtns[id]
        tag.checked = proxyItem.checked
        console.log(`end proxy ${proxyItem}`)
        if (proxyItem.checked)
        {
            proxyItem.parentNode.classList.add('tag-selected')
        }
        else
        {
            proxyItem.parentNode.classList.remove('tag-selected')
        }
    })

    if (!isTmp)
    {
        tagBtns[tagId].pinned = true
        tagProxyBtns[tagId] = btn
    }
    else
    {
        tmpTagProxyBtns[tagId] = btn
    }

    btn.classList.remove('vis-hide')
}

function removeTagFromPinList(tagId)
{
    if (tagId === '') { return }

    if (!tagProxyBtns.hasOwnProperty(tagId)) { return }

    tagProxyBtns[tagId].remove()
    delete tagProxyBtns[tagId]
}

function populatePinnedTags()
{
    const pins = document.querySelector('#tags-pins #buttons')
    for (const id of pinsList)
    {
        addTagToPinList(id, pins)
    }

    document.addEventListener('tag_click', e =>
    {
        const tagId = e.detail.tagId

        // PINNED tags
        if (tagProxyBtns.hasOwnProperty(tagId))
        {
            const proxy = tagProxyBtns[tagId]
            const proxyInput = tagProxyBtns[tagId].querySelector('input')
            proxyInput.checked = tagBtns[tagId].checked

            if (proxyInput.checked) {proxy.classList.add('tag-selected')}
            else { proxy.classList.remove('tag-selected') }

            return
        }

        if (tmpTagProxyBtns.hasOwnProperty(tagId))
        {

        }
    })

    document.addEventListener('tag_pin_click', e =>
    {
        const pinId = e.detail.tagId
        const pin = tagBtns[pinId]

        console.log(pin)
        console.log(pinsList)
        const index = pinsList.indexOf(pinId)
        if (index === -1)
        {
            pinsList.push(pinId)
            addTagToPinList(e.detail.tagId, pins)
        }
        else
        {
            pinsList.splice(index, 1)
            removeTagFromPinList(e.detail.tagId, pins)
        }

        pinsList.sort()
        localStorage.setItem(PINS, JSON.stringify(pinsList))

        console.log(pinsList)

        // quit if none
        if (pinsList.length === 0)
        {
            document.getElementById('tags-pins').classList.add('tags-pins-hide')
        }
        else
        {
            document.getElementById('tags-pins').classList.remove('tags-pins-hide')
        }
    })

    // quit if none
    if (pinsList.length === 0)
    {
        document.getElementById('tags-pins').classList.add('tags-pins-hide')
    }
}

function clearPinsList()
{
    pinsList = []
    document.getElementById('tags-pins').classList.add('tags-pins-hide')
    localStorage.setItem(PINS, JSON.stringify(pinsList))

    document.querySelectorAll('.tag-pin').forEach(elem => { elem.classList.remove('tag-pin-on') })
}



document.getElementById('tags-submit-add').addEventListener('click', submitAddTags)
document.getElementById('tags-submit-del').addEventListener('click', submitRemoveTags)
document.getElementById('tags-clear').addEventListener('click', clearTagsPopup)
document.getElementById('pins-clear').addEventListener('click', clearPinsList)
document.getElementById('tags-close').addEventListener('click', closeTagsPopup)
document.querySelector('.tags-popup-background').addEventListener('click', closeTagsPopup)

document.getElementById('tags-pins-submit-add').addEventListener('click', submitAddTags)
document.getElementById('tags-pins-submit-del').addEventListener('click', submitRemoveTags)
document.getElementById('tags-pins-clear').addEventListener('click', clearTagsPopup)

populatePinnedTags()

document.addEventListener('keydown', function(e)
{
    if (e.code === 'KeyT' && !e.shiftKey)
    {
        toggleTagsPopupDisplay()
    }
    else if (e.code === 'KeyN' && !e.shiftKey)
    {
        toggleTagsPinsDisplay()
    }
    else if (e.code === 'Escape' && !e.shiftKey)
    {
        closeTagsPopup()
    }
})