
var Base64Binary = {
	_keyStr: "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=",

	/* will return a  Uint8Array type */
	decodeArrayBuffer: function (input) {
		var bytes = (input.length / 4) * 3;
		var ab = new ArrayBuffer(bytes);
		this.decode(input, ab);

		return ab;
	},

	removePaddingChars: function (input) {
		var lkey = this._keyStr.indexOf(input.charAt(input.length - 1));
		if (lkey == 64) {
			return input.substring(0, input.length - 1);
		}
		return input;
	},

	decode: function (input, arrayBuffer) {
		//get last chars to see if are valid
		input = this.removePaddingChars(input);
		input = this.removePaddingChars(input);

		var bytes = parseInt((input.length / 4) * 3, 10);

		var uarray;
		var chr1, chr2, chr3;
		var enc1, enc2, enc3, enc4;
		var i = 0;
		var j = 0;

		if (arrayBuffer)
			uarray = new Uint8Array(arrayBuffer);
		else
			uarray = new Uint8Array(bytes);

		input = input.replace(/[^A-Za-z0-9\+\/\=]/g, "");

		for (i = 0; i < bytes; i += 3) {
			//get the 3 octects in 4 ascii chars
			enc1 = this._keyStr.indexOf(input.charAt(j++));
			enc2 = this._keyStr.indexOf(input.charAt(j++));
			enc3 = this._keyStr.indexOf(input.charAt(j++));
			enc4 = this._keyStr.indexOf(input.charAt(j++));

			chr1 = (enc1 << 2) | (enc2 >> 4);
			chr2 = ((enc2 & 15) << 4) | (enc3 >> 2);
			chr3 = ((enc3 & 3) << 6) | enc4;

			uarray[i] = chr1;
			if (enc3 != 64) uarray[i + 1] = chr2;
			if (enc4 != 64) uarray[i + 2] = chr3;
		}

		return uarray;
	}
}

function arrayBufferToBase64(arrayBuffer) {
    var base64 = ''
    var encodings = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

    var bytes = new Uint8Array(arrayBuffer)
    var byteLength = bytes.byteLength
    var byteRemainder = byteLength % 3
    var mainLength = byteLength - byteRemainder

    var a, b, c, d
    var chunk

    // Main loop deals with bytes in chunks of 3
    for (var i = 0; i < mainLength; i = i + 3) {
        // Combine the three bytes into a single integer
        chunk = (bytes[i] << 16) | (bytes[i + 1] << 8) | bytes[i + 2]

        // Use bitmasks to extract 6-bit segments from the triplet
        a = (chunk & 16515072) >> 18 // 16515072 = (2^6 - 1) << 18
        b = (chunk & 258048) >> 12 // 258048   = (2^6 - 1) << 12
        c = (chunk & 4032) >> 6 // 4032     = (2^6 - 1) << 6
        d = chunk & 63               // 63       = 2^6 - 1

        // Convert the raw binary segments to the appropriate ASCII encoding
        base64 += encodings[a] + encodings[b] + encodings[c] + encodings[d]
    }

    // Deal with the remaining bytes and padding
    if (byteRemainder == 1) {
        chunk = bytes[mainLength]

        a = (chunk & 252) >> 2 // 252 = (2^6 - 1) << 2

        // Set the 4 least significant bits to zero
        b = (chunk & 3) << 4 // 3   = 2^2 - 1

        base64 += encodings[a] + encodings[b] + '=='
    } else if (byteRemainder == 2) {
        chunk = (bytes[mainLength] << 8) | bytes[mainLength + 1]

        a = (chunk & 64512) >> 10 // 64512 = (2^6 - 1) << 10
        b = (chunk & 1008) >> 4 // 1008  = (2^6 - 1) << 4

        // Set the 2 least significant bits to zero
        c = (chunk & 15) << 2 // 15    = 2^4 - 1

        base64 += encodings[a] + encodings[b] + encodings[c] + '='
    }

    return base64
}

function createBinaryEditorDialog(prefix) {
    var dialog = $(
        "<div class=\"modal fade\" id=\"" + prefix + "Modal\" tabindex=\"-1\" aria-labelledby=\"" + prefix + "ModalLabel\" aria-hidden=\"true\">" +
            "<div class=\"modal-dialog modal-dialog-centered\">" +
                "<div class=\"modal-content\">" +
                    "<div class=\"modal-header\">" +
                        "<h5 class=\"modal-title\" id=\"" + prefix + "ModalLabel\">Browse for file</h5>" +
                        "<button type=\"button\" class=\"btn-close\" data-bs-dismiss=\"modal\" aria-label=\"Close\"></button>" +
                    "</div>" +
                    "<div class=\"modal-body\">" +
                        "<form><input type=\"file\" id=\"" + prefix + "_uploadInputField\" class=\"form-control\" /></form>" +
                    "</div>" +
                    "<div class=\"modal-footer\">" +
                        "<button type=\"button\" class=\"btn btn-primary\" id=\"" + prefix + "_saveChangesButton\" disabled>OK</button>" +
                    "</div>" +
                "</div>" +
            "</div>" +
        "</div>");

    document.body.appendChild(dialog[0]);
    return dialog;
}

function initializeBinaryEditor(prefix, default_download_name, on_content_change) {
    var dialog = createBinaryEditorDialog(prefix);
    var target = $("#" + prefix);
    var field = $("#" + prefix + "_uploadInputField");
    var saveButton = $("#" + prefix + "_saveChangesButton");
    var clearButton = $("#" + prefix + "_clearDataButton");
    var downloadButton = $("#" + prefix + "_downloadButton");
    var statusLabel = $("#" + prefix + "_presentStatus");
    var reader = new FileReader();

    function onContentChanged(binary_len) {
        var value = target[0].value;
        var exists = (value.length > 0);

        if (on_content_change !== undefined)
            on_content_change(value);

        if (binary_len < 0)
            binary_len = Base64Binary.decode(value).length;

        downloadButton.prop("disabled", !exists);
        downloadButton.removeClass(!exists ? "btn-outline-primary" : "btn-outline-secondary");
        downloadButton.addClass   ( exists ? "btn-outline-primary" : "btn-outline-secondary");
        clearButton.prop("disabled", !exists);
        clearButton.removeClass(!exists ? "btn-outline-danger" : "btn-outline-secondary");
        clearButton.addClass   ( exists ? "btn-outline-danger" : "btn-outline-secondary");

        // if (exists) {
        //     if (value.length > 10)
        //         value = value.substring(0, 10);
        //     value = value + "..."
        // }
        statusLabel.prop("innerText", exists ? "(" + binary_len + " bytes)" : "(empty)");
        if (exists)
            statusLabel.removeClass("text-muted");
        else
            statusLabel.addClass("text-muted");
    }

    reader.onload = function (ev) {
        saveButton.prop("disabled", false);
    };

    field.on("change", function () {
        saveButton.prop("disabled", true);

        if (this.files.length == 0)
            return;

        var file = this.files[0];
        reader.readAsArrayBuffer(file);
    });

    saveButton.on("click", function () {
        target.prop("value", arrayBufferToBase64(reader.result));
        onContentChanged(reader.result.byteLength);
        bootstrap.Modal.getInstance(dialog).hide();
    });

    clearButton.on("click", function () {
        target.prop("value", "");
        onContentChanged(0);
    });

    downloadButton.on("click", function () {
        var blob = new Blob([Base64Binary.decode(target[0].value)], { type: 'application/octet-stream' });

        const link = document.createElement('a');
        link.download = default_download_name;
        link.href = URL.createObjectURL(blob);

        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    onContentChanged(-1);
}
