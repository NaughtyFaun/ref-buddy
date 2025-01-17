import {waitForCondition}    from "/static/js/discover/utils.js"

/*
Source: https://stackoverflow.com/questions/2368784/draw-on-html5-canvas-using-a-mouse
 */
class DrawCanvas
{
    kActionMove = 0
    kActionDown = 1
    kActionUp   = 2
    kActionOut  = 3
    kHistoryLength = 50

    _imgId
    _canvas
    _ctx

    isDrawingMode
    _isDrawing
    _isErasing

    _brushColors = [
        "#ffffffff",
        "#ab0649",
        "#05a3b7ff",
        "#80e81b",
    ]

    _brushSizes = [
        1,
        1, 2, 3, 4,
        8, 16, 32, 64, 128, 256
    ]

    _brushes = [] // buttons

    _selectedColor = 1
    _lineWeight = 4
    _eraseWeight = 6

    _history = []
    _totalHistoryWrites = 0
    _lastStrokeCount = 0
    _undoSeq = false
    _tmpImg = new Image()

    prevX = 0
    currX = 0
    prevY = 0
    currY = 0

    constructor(selCnvId, selImg, selControls, imgId)
    {
        this._imgId = imgId
        this._canvas = document.querySelector(selCnvId)
        this._ctrls = document.querySelector(selControls)
        this._ctx = this._canvas.getContext("2d")

        this.initCanvas()
        this.initControls()
        // this.restoreFromSave()

        this._lastStrokeCount = 1
        this.recordHistory()
    }

    updateCanvas(selImg)
    {
        const img = document.querySelector(selImg)

        waitForCondition(() => img.width > 0 && img.height > 0)(img).then(initImg => {
            this._canvas.width = initImg.width
            this._canvas.height = initImg.height

            this.fillMark()
        })
    }

    initCanvas()
    {
        // console.log(`initializing canvas`)

        this._canvas.addEventListener("mousemove", (evt) => {this.drawByCoord(this.kActionMove, evt)}, false)
        this._canvas.addEventListener("mousedown", (evt) => {this.drawByCoord(this.kActionDown, evt)}, false)
        this._canvas.addEventListener("mouseup",   (evt) => {this.drawByCoord(this.kActionUp,   evt)}, false)
        this._canvas.addEventListener("mouseout",  (evt) => {this.drawByCoord(this.kActionOut,  evt)}, false)

        this.setColor(this._selectedColor)
        this.setLineWeight(this._lineWeight)
    }

    initControls()
    {
        let elem = this._ctrls.querySelector('#draw-eraser')
        elem.addEventListener("click", (evt) =>
        {
            this._isErasing = true
            this.setColor(0)
            this.updateBrushesUI(evt.target)
        })
        this._brushes.push(elem)

        elem = this._ctrls.querySelector('#draw-clear')
        elem.addEventListener("click", (evt) => { this.clear() })

        elem = this._ctrls.querySelector('#draw-weight')
        elem.value = this._lineWeight
        elem.addEventListener("change", (evt) => { this.setLineWeight(parseInt(evt.target.value)) })

        elem = this._ctrls.querySelector('#erase-weight')
        elem.value = this._eraseWeight
        elem.addEventListener("change", (evt) => { this.setEraseWeight(parseInt(evt.target.value)) })

        // color buttons
        elem = this._ctrls.querySelector('#tlp-draw-clr')
        for (let i = 1; i < this._brushColors.length; i++)
        {
            let clr = elem.cloneNode()
            clr.value = i
            clr.textContent = "C" + i
            clr.id = clr.textContent
            clr.style.backgroundColor = this._brushColors[i]
            clr.addEventListener("click", (evt) =>
            {
                this._isErasing = false
                this.updateBrushesUI(evt.target)
                this.setColor(evt.target.value)
            })
            clr.classList.remove("hidden")
            elem.before(clr)
            this._brushes.push(clr)
        }
        this.updateBrushesUI(this._brushes[1])
    }

    toggle()
    {
        this.setDrawingMode(this._canvas.classList.contains('hidden'))
    }

    setDrawingMode(isOn)
    {
        if (isOn)
        {
            this._canvas.classList.remove('hidden')
            this._ctrls.classList.remove('hidden')
            this.isDrawingMode = true
        }
        else
        {
            this._canvas.classList.add('hidden')
            this._ctrls.classList.add('hidden')
            this.isDrawingMode = false
        }
    }

    setColor(id)
    {
        this._selectedColor = id

        if (id === 0)
        {
            this._ctx.globalCompositeOperation = 'destination-out'
        }
        else
        {
            this._ctx.globalCompositeOperation = 'source-over'
        }
    }

    setLineWeight(w)
    {
        this._lineWeight = w

        this._ctrls.querySelector('label[for="draw-weight"] .size').textContent = this._brushSizes[w]
    }

    setEraseWeight(w)
    {
        this._eraseWeight = w

        this._ctrls.querySelector('label[for="erase-weight"] .size').textContent = this._brushSizes[w]
    }

    fillMark()
    {
        this._ctx.rect(0, 0, this._canvas.width * 0.01, this._canvas.width * 0.01)
        this._ctx.fillStyle = "#509336"
        this._ctx.fill()
    }

    clear() {
        if (!confirm("Want to clear")) return

        this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height)
    }

    updateBrushesUI(selected)
    {
        selected.classList.add('draw-selected')
        for (const b of this._brushes)
        {
            if (selected === b) continue
            b.classList.remove('draw-selected')
        }
    }

    // save()
    // {
    //     document.getElementById("canvasimg").style.border = "2px solid";
    //     var dataURL = canvas.toDataURL();
    //     document.getElementById("canvasimg").src = dataURL;
    //     document.getElementById("canvasimg").style.display = "inline";
    // }

    drawByCoord(action, evt)
    {
        if (!this.isDrawingMode) return

        if (action === this.kActionMove && this._isDrawing)
        {
            this.prevX = this.currX
            this.prevY = this.currY
            this.currX = evt.clientX - this._canvas.offsetLeft
            this.currY = evt.clientY - this._canvas.offsetTop
            this.realDraw()
        }
        else if (action === this.kActionDown && !this._isDrawing)
        {
            this.prevX = this.currX
            this.prevY = this.currY
            this.currX = evt.clientX - this._canvas.offsetLeft
            this.currY = evt.clientY - this._canvas.offsetTop

            this._isDrawing = true
            this._lastStrokeCount = 0
        }
        else if (action === this.kActionUp || action === this.kActionOut)
        {
            this._isDrawing = false

            this.recordHistory()
            this._lastStrokeCount = 0
        }
    }

    realDraw()
    {
        this._ctx.beginPath();
        this._ctx.lineCap = "round";
        this._ctx.moveTo(this.prevX, this.prevY);
        this._ctx.lineTo(this.currX, this.currY);
        this._ctx.strokeStyle = this._brushColors[this._selectedColor];
        this._ctx.lineWidth = this._brushSizes[this._isErasing ? this._eraseWeight : this._lineWeight];
        this._ctx.stroke();

        this._lastStrokeCount++
    }

    recordHistory()
    {
        if (!this.isDrawingMode) return
        if (this._lastStrokeCount === 0) return

        this._undoSeq = false
        this._canvas.toBlob((blob) =>
        {
            this._history.push(blob)

            if (this._history.length < this.kHistoryLength) return
            this._history.shift()
        })

        this._totalHistoryWrites++

        // this.saveHistory()
    }

    undo()
    {
        if (!this.isDrawingMode) return
        if (this._history.length === 0) return

        // I save stroke right after it has been done, so in order to undo,
        // first I have to remove CURRENT canvas
        if (!this._undoSeq)
        {
            this._undoSeq = true
            this._history.pop()
        }

        const blob = this._history.pop()
        const url = URL.createObjectURL(blob)
        this._tmpImg.onload = () =>
        {
            URL.revokeObjectURL(url)
            this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height)
            this._ctx.drawImage(this._tmpImg, 0, 0)
        }
        this._tmpImg.src = url

        // make sure we have at least 1 element in the undo
        if (this._history.length === 0) this._history.push(blob)

        // this.saveHistory()
    }

    // saveHistory()
    // {
    //     console.log('write1 '+ this._totalHistoryWrites)
    //     if (this._totalHistoryWrites <= 1) return
    //
    //     let reader = new FileReader();
    //     reader.readAsArrayBuffer(this._history[this._history.length-1]);
    //     reader.onloadend = function ()
    //     {
    //         let base64data = btoa(String.fromCharCode.apply(null, new Uint8Array(reader.result)))
    //         localStorage.setItem(`draw_history_${this._imgId}`, base64data)
    //     }
    // }

    // restoreFromSave()
    // {
    //     const url = localStorage.getItem(`draw_history_${this._imgId}`)
    //     if (url === null) return
    //
    //     console.log('read '+ url)
    //
    //     this._tmpImg.onload = () =>
    //     {
    //         this._ctx.clearRect(0, 0, this._canvas.width, this._canvas.height)
    //         this._ctx.drawImage(this._tmpImg, 0, 0)
    //     }
    //     this._tmpImg.src = url
    // }
}

export { DrawCanvas }