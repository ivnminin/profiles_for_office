Dropzone.options.dropper = {
    dictDefaultMessage: "Нажмите в данное поле и выберете скриншоты.  Количество файлов не больше 5 шт., " +
        "максимальный размер одного файла не больше 5 Мб.",
    paramName: 'file',
    autoProcessQueue: false,
    addRemoveLinks: true,
    createImageThumbnails: false,
    chunking: true,
    forceChunking: true,
    url: '/upload',
    parallelUploads: 20,
    maxFilesize: 5, // megabytes
    maxFiles: 5,
    chunkSize: 5000000, // bytes
    autoDiscover: false,

    accept: function (file, done) {
        if (file.size === 0) {
            done("Пустой файл не будет загружен");
        } else {
            done();
        }
    },

    init: function () {
        // this.on("maxfilesexceeded", function(file){
        //     if (!alert_msg) {
        //         alert("Вы добавили много файлов, лишние не буду добавлены в заявку! " +
        //               "Количество файлов не больше 5 шт., максимальный размер одного файла не больше 5 Мб.");
        //     }
        // });
        var myDropzone = this;

        myDropzone.on("error", function (file, message) {
            alert(' Файл с именем ' + file.name + ' не будет добавлен, так как он не отвечает требованиям. '
                + message);
            this.removeFile(file);
        });

        $('#id_dropzone').on("submit", function (e) {

            e.preventDefault();

            var title = document.querySelector('input[name="title"]');
            var description = document.querySelector('textarea[name="description"]');
            var order = document.querySelector('input[name="order"]');

            this.formData = new FormData();
            this.formData.append("title", title.value);
            this.formData.append("description", description.value);
            if (order) {
                this.formData.append("order_id", order.value);
            }
            this._csrftoken = document.querySelector('input[name="csrf_token"]').value;
            var xhr = new XMLHttpRequest();
            xhr.open("POST", "/form");
            xhr.setRequestHeader('X-CSRFToken', this._csrftoken);
            var errMsg = 'Что то пошло не так, попробуйте позже.';
            xhr.onreadystatechange = function () {
                if (xhr.readyState === 4) {
                    if (xhr.status === 200) {
                        document.querySelector('input[name="title"]').readOnly = true;
                        document.querySelector('textarea[name="description"]').readOnly = true;
                        var response_good = JSON.parse(xhr.responseText);

                        var filesOnlyError = false;

                        for (var i=0; i < myDropzone.files.length; i++) {
                            if (myDropzone.files[i].status === 'queued') {
                                filesOnlyError = true;
                            }
                        }

                        if (myDropzone.files.length > 0 && filesOnlyError) {
                            myDropzone.response_ = response_good;
                            myDropzone.processQueue();
                        } else {
                            window.location.href = response_good.data.url;
                        }
                    } else if (xhr.status === 404) {
                        var response_bad = JSON.parse(xhr.responseText);
                        var error_title = document.querySelector('p[class="error-title"]');
                        var error_description = document.querySelector('p[class="error-description"]');
                        // error_title.innerText = response_bad.errors.title;
                        // error_description.innerText = response_bad.errors.description;
                        error_title.innerText = response_bad.errors.title;
                        error_description.innerText = response_bad.errors.description;
                    } else {
                        alert(errMsg);
                    }
                }

            };
            xhr.send(this.formData);
        });
        myDropzone.on("sending", function (file, xhr, formData) {
            console.log('sending the end!');
            formData.append("title", this.response_.data.title);
            formData.append("description", this.response_.data.description);
            formData.append("order_id", this.response_.data.order);

        });
        myDropzone.on("queuecomplete", function (file, xhr, formData) {
            console.log('queuecomplete the end!');
            try {
                window.location.href = this.response_.data.url;
            } catch (e) {
                console.log('error - e.name: ' + e.name + ', msg: ' + e.message);
            }
        });
        myDropzone.on("complete", function (file, xhr, formData) {
            console.log('complete the end!');
        });
    },
};
