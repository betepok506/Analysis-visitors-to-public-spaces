var myCanvas = document.getElementById("myCanvas");
myCanvas.width = 300;
myCanvas.height = 300;

var ctx = myCanvas.getContext("2d");

function drawLine(ctx, startX, startY, endX, endY,color){
    ctx.save();
    ctx.strokeStyle = color;
    ctx.beginPath();
    ctx.moveTo(startX,startY);
    ctx.lineTo(endX,endY);
    ctx.stroke();
    ctx.restore();
}

function drawBar(ctx, upperLeftCornerX, upperLeftCornerY, width, height,color){
    ctx.save();
    ctx.fillStyle=color;
    ctx.fillRect(upperLeftCornerX,upperLeftCornerY,width,height);
    ctx.restore();
}

var myVinyls = {
    "Classical music": 10,
    "Alternative rock": 14,
    "Pop": 2,
    "Jazz": 12
};

var Barchart = function(options){
    this.options = options;
    this.canvas = options.canvas;
    this.ctx = this.canvas.getContext("2d");
    this.colors = options.colors;

    this.draw = function(){
        var maxValue = 0;
        for (var categ in this.options.data){
            maxValue = Math.max(maxValue,this.options.data[categ]);
        }
        var canvasActualHeight = this.canvas.height - this.options.padding * 2;
        var canvasActualWidth = this.canvas.width - this.options.padding * 2;

        //drawing the grid lines
        var gridValue = 0;
        while (gridValue <= maxValue){
            var gridY = canvasActualHeight * (1 - gridValue/maxValue) + this.options.padding;
            drawLine(
                this.ctx,
                0,
                gridY,
                this.canvas.width,
                gridY,
                this.options.gridColor
            );

            //writing grid markers
            this.ctx.save();
            this.ctx.fillStyle = this.options.gridColor;
            this.ctx.textBaseline="bottom";
            this.ctx.font = "bold 10px Arial";
            this.ctx.fillText(gridValue, 10,gridY - 2);
            this.ctx.restore();

            gridValue+=this.options.gridScale;
        }

        //drawing the bars
        var barIndex = 0;
        var numberOfBars = Object.keys(this.options.data).length;
        var barSize = (canvasActualWidth)/numberOfBars;

        for (categ in this.options.data){
            var val = this.options.data[categ];
            var barHeight = Math.round( canvasActualHeight * val/maxValue) ;
            drawBar(
                this.ctx,
                this.options.padding + barIndex * barSize,
                this.canvas.height - barHeight - this.options.padding,
                barSize,
                barHeight,
                this.colors[barIndex%this.colors.length]
            );

            barIndex++;
        }

        //drawing series name
        this.ctx.save();
        this.ctx.textBaseline="bottom";
        this.ctx.textAlign="center";
        this.ctx.fillStyle = "#000000";
        this.ctx.font = "bold 14px Arial";
        this.ctx.fillText(this.options.seriesName, this.canvas.width/2,this.canvas.height);
        this.ctx.restore();

        //draw legend
        barIndex = 0;
        var legend = document.querySelector("legend[for='myCanvas']");
        var ul = document.createElement("ul");
        legend.append(ul);
        for (categ in this.options.data){
            var li = document.createElement("li");
            li.style.listStyle = "none";
            li.style.borderLeft = "20px solid "+this.colors[barIndex%this.colors.length];
            li.style.padding = "5px";
            li.textContent = categ;
            ul.append(li);
            barIndex++;
        }
    }
}


var myBarchart = new Barchart(
    {
        canvas:myCanvas,
        seriesName:"Vinyl records",
        padding:20,
        gridScale:5,
        gridColor:"#eeeeee",
        data:myVinyls,
        colors:["#a55ca5","#67b6c7", "#bccd7a","#eb9743"]
    }
);



function check_param(){
    var ok = true;
    if(Number.isNaN(Number(document.forms['camera']['fps'].value)) || 
        Number(document.forms['camera']['fps'].value)<=0)
    {   
        ok=false;
        document.forms['camera']['fps'].style.borderColor = "red";
    }
    if(Number.isNaN(Number(document.forms['camera']['max_dist_bboxes'].value)) ||
        Number(document.forms['camera']['max_dist_bboxes'].value)<=0)
    { 
        ok=false;
        document.forms['camera']['max_dist_bboxes'].style.borderColor = "red";
    }
    if(Number.isNaN(Number(document.forms['camera']['min_square_bboxes'].value)) ||
        Number(document.forms['camera']['min_square_bboxes'].value)<=0)
    { 
        ok=false;
        document.forms['camera']['min_square_bboxes'].style.borderColor = "red";
    }
    if(Number.isNaN(Number(document.forms['camera']['time_delete_tracking'].value)) ||
        Number(document.forms['camera']['time_delete_tracking'].value) <= 0)
    { 
        ok=false;
        document.forms['camera']['time_delete_tracking'].style.borderColor = "red";
    }
    return ok;
}

function check_param_editing(form_){
    var ok = true;
    if(Number.isNaN(Number(form_['fps'].value)) || 
        Number(form_['fps'].value)<=0)
    {   
        ok=false;
        form_['fps'].style.borderColor = "red";
    }

    if(form_['name_cam'].value == '')
    {   
        ok=false;
        form_['name_cam'].style.borderColor = "red";
    }

    if(Number.isNaN(Number(form_['max_dist_bboxes'].value)) ||
        Number(form_['max_dist_bboxes'].value)<=0)
    { 
        ok=false;
        form_['max_dist_bboxes'].style.borderColor = "red";
    }
    if(Number.isNaN(Number(form_['min_square_bboxes'].value)) ||
        Number(form_['min_square_bboxes'].value)<=0)
    { 
        ok=false;
        form_['min_square_bboxes'].style.borderColor = "red";
    }
    if(Number.isNaN(Number(form_['time_delete_tracking'].value)) ||
        Number(form_['time_delete_tracking'].value) <= 0)
    { 
        ok=false;
        form_['time_delete_tracking'].style.borderColor = "red";
    }
    return ok;
}

function button_click_onkeyup(Object){
    Object.style.border ="1px solid black" ;
}

function log(html) {
    document.getElementById('log_upload').innerHTML = html;
}

function button_click_camera(button){
    var name_button = button['name'];
    if(name_button=='add'){
        x = document.getElementById('camera');
        
        if(check_param()==false) return;
        if(document.getElementById('load_video_setting').style.display=='none'){
            if(x['url'].value == ""){
                console.log('Введите ссылку на видео поток!');
                return false;
            } 
        }else{
            if(x['file'].files.length == 0){
                console.log('Файл не обнаружен!');
                return false;
            }
        }
        
        if(document.getElementById('rabbit_header') == null){
            // Пост запрос с сообщением об ошибке хедер не найденж
            return false;
        }

       
        xhr = new XMLHttpRequest();

        xhr.upload.onprogress = function(event) {
            log(event.loaded + ' / ' + event.total + 'байт');
        }

        xhr.onload = xhr.onerror = function() {
            if (this.status == 200) {
                log("Загрузка завершена");
                let block = document.getElementById('hide_array2');
                block.style.display = 'none';
                sessionStorage.setItem('block_add_cam', false);
                block = document.getElementsByClassName('show_add_cam')[0];
                block.style.display = 'flex';

                setTimeout(function(){
                    location.reload();
                }, 2000);
            } else {
              log("Ошибка " + this.status);
            }
        };

        xhr.open('post', '/create_camera')
        formData = new FormData();

        inputs = document.forms['camera'].getElementsByTagName("input");
        options = document.forms['camera'].getElementsByTagName("option");
        
        for(var i = 0; i < inputs.length; i++)
        {
            if(inputs[i].name!='file'){
                formData.append(inputs[i].name,inputs[i].value);
            }else
            {
                formData.append(inputs[i].name,inputs[i].files[0]);
            }
        }
        
        for(var i = 0; i < options.length; i++)
            formData.append(options[i].id,options[i].value);
        
       
        xhr.send(formData);
    }
    else if(name_button == 'delete')
    {
        let block = document.getElementById('hide_array2');
        block.style.display = 'none';
        sessionStorage.setItem('block_add_cam', false);
        block = document.getElementsByClassName('show_add_cam')[0];
        block.style.display = 'flex';
    }
}

// function button_click_add_bd_cam() {
//     if(check_param()==false) return;
//     xhr = new XMLHttpRequest();

//     xhr.open('post', '/check_selected')
//     x = document.getElementById('camera')
//     formData = new FormData();

//     console.log(document.forms['camera']['file'].formData);
//     inputs = document.forms['camera'].getElementsByTagName("input");
//     options = document.forms['camera'].getElementsByTagName("option");
//     for(var i = 0; i < inputs.length; i++)
//     {
//         if(inputs[i].name!='file'){
//             formData.append(inputs[i].name,inputs[i].value);
//         }else{
//             formData.append(inputs[i].name,inputs[i].files[0]);
//         }
//     }
    
//     for(var i = 0; i < options.length; i++)
//         formData.append(options[i].id,options[i].value);

//     xhr.send(formData);
//     // Реализовать удалиние блока после добавления камеры
// }

function get_element_create_cam(form_){
    if(check_param_editing(form_)){
        url = form_['url'].value;
        ts = form_['ts'].value;
        

        if(document.getElementById('load_video_setting').style.display=='none'){
            ts = -1;
            video = None;
        }else{
            url = "";
            video = form_['file'].files[0];
        }
        return  {'ts':ts,
                'url':url,
                'name_cam':form_['name_cam'].value,
                'header': form_['rabbit_header'].value,
                'fps':form_['fps'].value,
                'video': video,
                'polygons':form_['polygons'].value,
                'max_dist_bboxes':form_['max_dist_bboxes'].value,
                'min_square_bboxes':form_['min_square_bboxes'].value,
                'time_delete_tracking':form_['time_delete_tracking'].value}
    }
    return false;
}

function button_click_save_editing_setting(){
    xhr = new XMLHttpRequest();

    xhr.open('post', '/editing_setting')
    formData = new FormData();

    inputs = document.forms['editing_setting'].getElementsByTagName("input");

    for(var i = 0; i < inputs.length; i++)
    {
        formData.append(inputs[i].name,inputs[i].value);
    }
    xhr.send(formData);
    setTimeout(function(){
        location.reload();
    }, 2000);
}

function load_map(){

    xhr = new XMLHttpRequest();

    xhr.open('post', '/load_map')
    formData = new FormData();

    inputs = document.forms['form_load_map'].getElementsByTagName("input");

    formData.append(inputs[0].name,inputs[0].files[0]);
    
    xhr.send(formData);

    setTimeout(function(){
        location.reload();
    }, 2000);
}


function load_markup(){

    xhr = new XMLHttpRequest();

    xhr.open('post', '/load_markup')
    formData = new FormData();

    inputs = document.forms['form_load_markup'].getElementsByTagName("input");

    formData.append(inputs[0].name,inputs[0].files[0]);
    
    xhr.send(formData);

    setTimeout(function(){
        location.reload();
    }, 2000);
}

function button_click_add_polygons(button){
    var array = button.name.split('_')
    id = array[array.length-1];
    

    x = document.getElementsByName('list_polygons_'+id)[0];
    var elemDiv = document.createElement('div');
    elemDiv.className = 'polygons_item';
    elemDiv.name = "polygons_item_" + id;

    cur_elem = x.getElementsByClassName('polygons_item');
    var list_polygons = []

    for(var i =0 ; i<cur_elem.length ; i++){
        list_polygons.push({'polygons':cur_elem[i].getElementsByClassName('polygons_coord')[0].value,
                            'id_cam':cur_elem[i].getElementsByClassName('id_cam')[0].value});
    }
    list_polygons.push({'polygons':'',
                            'id_cam':''});

    update_session_storage_polygons(list_polygons,id);

    id_elem = cur_elem.length+1;
    
    elemDiv.id = "polygons_item_" + id_elem;
    
    elemDiv.innerHTML = `<div> \
                            <label for="polygons">Полигон</label> \
                            <input type="text" onchange="validation_polygons(this)" class='polygons_coord' name = "polygons_${id}">\
                        </div>\
                        <div>\
                            <label for="polygons">Номер зоны</label> \
                            <input type="number" onchange="validation_polygons(this)" class='id_cam' name = "id_cam_${id}">\
                        </div> \
                        <div> \
                            <span class="closebtn" id="${id}_${id_elem}" \
                            onclick="span_click_closebtn(this)">&times;</span> \
                        </div>`
    x.appendChild(elemDiv);
    
}

function update_session_storage_polygons(list_polygons, id){
    if(list_polygons==null)return;
    let dict_polygons = JSON.parse(sessionStorage.getItem('polygons_add'));

    if(dict_polygons== null){
        dict_polygons = new Object()
    }
    dict_polygons[id] = list_polygons;

    sessionStorage.setItem('polygons_add', JSON.stringify(dict_polygons));
}

function validation_polygons(button){
    console.log(button);
    var array = button.name.split('_');
    var id = array[array.length-1];

    cur_elem = document.getElementsByName('list_polygons_'+id)[0];
    cur_elem = cur_elem.getElementsByClassName('polygons_item');
    
    var list_polygons = []

    for(var i =0 ; i < cur_elem.length ; i++){
        list_polygons.push({'polygons':cur_elem[i].getElementsByClassName('polygons_coord')[0].value,
                            'id_cam':cur_elem[i].getElementsByClassName('id_cam')[0].value});
    }
    update_session_storage_polygons(list_polygons,id);
    
}

function span_click_closebtn(span){
    var array = span.id.split('_');
    id_div = array[0];
    id_item = array[1];
    

    x = document.getElementsByName('list_polygons_'+id_div)[0];
    x.removeChild(x.querySelector(`#polygons_item_${id_item}`));

    cur_elem = x.getElementsByClassName('polygons_item');
    var list_polygons = []
    for(var i =0 ; i < cur_elem.length ; i++){
        list_polygons.push({'polygons':cur_elem[i].getElementsByClassName('polygons_coord')[0].value,
                            'id_cam':cur_elem[i].getElementsByClassName('id_cam')[0].value});
        
    }
    update_session_storage_polygons(list_polygons, id_div);
    draw_polygon(id_div);

}

function draw_polygon(id){

    inputs = document.getElementsByName('polygons_'+id);
    cam_id = document.getElementsByName('id_cam_'+id);
 
    x = document.getElementsByClassName('img_polygons_'+id)[0];
    img_width = x.width;
    img_height = x.height;

    class_map = document.getElementsByName('map_'+id)[0];
    class_map.style.width = ''+img_width+'px'
    class_map.style.height = 'auto';

    node_map = document.getElementsByName('svg_map_'+id)[0];
    list_path = node_map.getElementsByClassName('map_path');

    mas_len = list_path.length;
    for(var i = 0 ; i< mas_len;i++){
        node_map.removeChild(list_path[0]);
    }

    for(var i = 0; i < inputs.length; i++){
            elem = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            elem.setAttribute('d',inputs[i].value);
            elem.setAttribute('style', 'opacity: 0.55; fill: green; title:'+cam_id[i].value);
            elem.setAttribute('class', 'map_path');
            elem.title = cam_id[i].value;
            node_map.appendChild(elem);
        
    }

}

function button_click_draw_polygons(button){
    var array = button.name.split('_');
    id = array[array.length-1];
    draw_polygon(id);
}

// function button_click_show_polygons_list(){
//     xhr = new XMLHttpRequest();
//     form_ = document.forms['camera'];

//     xhr.open('post', '/create_camera')
//     xhr.send();
//     xhr.onload = function() {
//         if (xhr.status != 200) { // анализируем HTTP-статус ответа, если статус не 200, то произошла ошибка
//           alert(`Ошибка ${xhr.status}: ${xhr.statusText}`); // Например, 404: Not Found
//         } else { // если всё прошло гладко, выводим результат
//           alert(`Готово, получили ${xhr.response.length} байт`); // response -- это ответ сервера
//         }
//       };
// }

function button_click_events_process(button){

    var action, id;
    var array = button.name.split('_');
    action = array[0];
    id = array[1];
    if(action == 'editing-polygons'){
        node_polygons = document.getElementsByClassName('polygons_'+id)[0];
        document.getElementsByClassName('camera_'+ id)[0].style.display='none';
        document.getElementsByClassName('get_video_'+id)[0].style.display='none';

        if(node_polygons.style.display == 'none'){
            node_polygons.style.display = 'flex';
            cur_elem = document.getElementsByName('list_polygons_'+id)[0];
            cur_elem = cur_elem.getElementsByClassName('polygons_item');
            
            var list_polygons = []

            for(var i =0 ; i < cur_elem.length ; i++){
                list_polygons.push({'polygons':cur_elem[i].getElementsByClassName('polygons_coord')[0].value,
                                    'id_cam':cur_elem[i].getElementsByClassName('id_cam')[0].value});
            }
            update_session_storage_polygons(list_polygons,id);
        }else{
            node_polygons.style.display = 'none';
            let dict_polygons = JSON.parse(sessionStorage.getItem('polygons_add'));

            if(dict_polygons== null){
                dict_polygons = new Object()
            }

            delete dict_polygons[id]; 
            sessionStorage.setItem('polygons_add', JSON.stringify(dict_polygons));
            return;
        }

        var request = new XMLHttpRequest();
        request.open('GET', `/events_process?action=editing-polygons&id_cam=${id}`);
        request.responseType = 'text';
        

        request.onload = function() {

                load_json = JSON.parse(request.response)

                node_list_polygons = document.getElementsByName(`list_polygons_${id}`)[0];
                mas_polygons_items = node_list_polygons.getElementsByClassName('polygons_item');
                len = mas_polygons_items.length
                for(var i =0;i<len;i++){
                    node_list_polygons.removeChild(mas_polygons_items[0]);
                }

                id_elem = 1;
                for(var i =0;i<load_json['polygons'].length;i++){
                        var elemDiv = document.createElement('div');
                        elemDiv.className = 'polygons_item';
                        elemDiv.name = "polygons_item_" + id_elem;
                        elemDiv.id = "polygons_item_" + id_elem;
                        
                        var Div_ = document.createElement('div');
                        var label_ = document.createElement('label');
                        label_.innerText = 'Полигон';
                        label_.setAttribute('for','polygons');
                        
                        var input_ = document.createElement('input');
                        input_.setAttribute('class', 'polygons_coord');
                        input_.setAttribute('type', 'text');
                        input_.setAttribute('name', 'polygons_'+id);
                        input_.value = load_json['polygons'][i];
                        input_.onchange = function () {  
                            validation_polygons(this);
                        };

                        Div_.appendChild(label_);
                        Div_.appendChild(input_);
                        elemDiv.appendChild(Div_);

                        Div_ = document.createElement('div');
                        label_ = document.createElement('label');
                        label_.innerText = 'Номер зоны';
                        label_.setAttribute('for','polygons');

                        input_ = document.createElement('input');
                        input_.setAttribute('type', 'number');
                        input_.setAttribute('class', 'id_cam');
                        input_.setAttribute('name', 'id_cam_'+id);
                        input_.value = load_json['area_id'][i];
                        input_.onchange = function () {  
                            validation_polygons(this);
                        };

                        Div_.appendChild(label_);
                        Div_.appendChild(input_);
                        elemDiv.appendChild(Div_);

                        Div_ = document.createElement('div');
                        Div_.innerHTML = `<span class="closebtn" id="${id}_${id_elem}" \
                                                onclick="span_click_closebtn(this)">&times;</span> `
                        
                        elemDiv.appendChild(Div_);

                        node_list_polygons.appendChild(elemDiv);
                        id_elem+=1;
                }

                list_polygons = []

                for(var i=0;i<load_json['polygons'].length;i++){
                    list_polygons.push({'polygons':load_json['polygons'][i],
                                        'id_cam': load_json['area_id'][i]});
                }

                update_session_storage_polygons(list_polygons,id)
                draw_polygon(id);
                
        };
        request.send();

    }else if(action =='save'){
        var request = new XMLHttpRequest();
        request.open('POST', `/events_process`);
        formData = new FormData();
        node = document.getElementsByClassName('camera_'+ id)[0];
        inputs = node.getElementsByTagName('input');
        inputs_elem = new Object()

        for(var i = 0;i<inputs.length;i++){
            inputs_elem[inputs[i].name] = inputs[i].value;
        }


        if(true){
            data= {'name_cam': inputs_elem['name_cam'],
                    'ts':inputs_elem['ts'],
                    'fps':inputs_elem['fps'],
                    'polygons':inputs_elem['polygons'],
                    'max_dist_bboxes':inputs_elem['max_dist_bboxes'],
                    'min_square_bboxes':inputs_elem['min_square_bboxes'],
                    'time_delete_tracking':inputs_elem['time_delete_tracking']
                }
        }else{
            return false;
        }

        formData.append('cam_id',id);
        formData.append('action',action);
        formData.append('data',JSON.stringify(data));
        request.send(formData);

    }else if(action=='editing'){
        node = document.getElementsByClassName('camera_'+ id)[0];
        document.getElementsByClassName('polygons_'+id)[0].style.display='none';
        document.getElementsByClassName('get_video_'+id)[0].style.display='none';
        
        if (node.style.display =='block')
        {
            node.style.display='none'
            return;
        }
        node.style.display ='block';
        var request = new XMLHttpRequest();
        request.open('GET', `/events_process?action=editing&id_cam=${id}`);
        request.responseType = 'text';
        

        request.onload = function() {
            console.log(request.response);
            load_json = JSON.parse(request.response);
            node = document.getElementsByClassName('camera_'+ id)[0];

            list_input = node.getElementsByTagName('input');
            list_input.name_cam.value = load_json['name_cam'];
            list_input.ts.value = load_json['start_ts'];
            list_input.fps.value = load_json['fps'];
            // list_input.polygons.value = load_json['polygons'];
            list_input.max_dist_bboxes.value = load_json["max_dist_between_bbox"];
            list_input.min_square_bboxes.value = load_json['min_square_bbox'];
            list_input.time_delete_tracking.value = load_json['cnt_fps_del'];
            
        };

        request.send();
    }
    else if(action == 'get-video'){
        node = document.getElementsByClassName('get_video_'+id)[0];

        document.getElementsByClassName('polygons_'+id)[0].style.display='none';
        document.getElementsByClassName('camera_'+ id)[0].style.display='none';

        if(node.style.display == 'none'){
            node.style.display = 'flex';

        }else{
            node.style.display = 'none';
            return;
        }
    }
    else{
        document.getElementsByClassName('get_video_'+id)[0].style.display='none';
        document.getElementsByClassName('polygons_'+id)[0].style.display='none';
        document.getElementsByClassName('camera_'+ id)[0].style.display='none';

        var request = new XMLHttpRequest();
        request.open('POST', `/events_process`);
        formData = new FormData();
        formData.append('cam_id',id);
        formData.append('action',action);
        request.send(formData);
    }
    return false;
}

function create_data(ts){
    parts = ts.split(" ")
    part_one = parts[0]
    part_two = parts[1]
    part_year = part_one.split('-')
    part_time = part_two.split('-')
    return new Date(part_year[0], part_year[1] - 1, part_year[2],
                    part_time[0], part_time[1], part_time[2]);
}

function button_click_create_video(button){
    console.log("Opening the SSE connection")
    
    ts_start = document.getElementById('ts_start_'+button.name).value;
    ts_end = document.getElementById('ts_end_'+button.name).value;
    datetime_start_ts = create_data(ts_start);
    datetime_end_ts = create_data(ts_end);

    if (datetime_start_ts > datetime_end_ts){
        document.getElementById('ts_start_'+button.name).style.border = '3px solid red';
        document.getElementById('ts_end_'+button.name).style.border = '3px solid red';
        return;
    }

    document.getElementById('ts_start_'+button.name).style.border = '';;
    document.getElementById('ts_end_'+button.name).style.border = '';

    document.getElementById('button_show_last_video_'+button.name).style.display='none';

    var source = new EventSource(`/progress/${button.name}_${ts_start}_${ts_end}`);
    source.onmessage = function(event) {
        sent_data = JSON.parse(event.data)
        // console.log(sent_data)
        var done = true
        for (i in sent_data) {
            // console.log(i, sent_data[i])
            
            // data received is in the form : {'0':value, '1':value}
            qi = "#prog_"+button.name
            $(qi).css('width', sent_data[i]+'%').attr('aria-valuenow', sent_data[i]);
            lqi = qi+"_label"
            $(lqi).text(sent_data[i]+'%');
            if (sent_data[i] < 99)
                done = false
        }
        
        if(done){
            qi = "#prog_"+button.name
            $(qi).css('width', 100+'%').attr('aria-valuenow', 100);
            lqi = qi+"_label"
            $(lqi).text('Обработка завершена!');
            document.getElementById('button_show_last_video_'+button.name).style.display='block';
            source.close()
        }
        
    }
}

function button_click_last_video(button){
    node = document.getElementById('video_'+button.name);
    if(node.style.display == 'none'){
        node.style.display = 'flex';
        node.style.margin = '30px 0px 30px 0px';
    }else{
        node.style.display = 'none';
        node.style.margin = '0px 0px 0px 0px';
        return;
    }
}


function button_click_save_polygons(button){
    let action, id;
    array = button.name.split('_');
    action = array[0];
    id = array[1];
    inputs = document.getElementsByName('polygons_'+id);
    area_id = document.getElementsByName('id_cam_'+id);
    formData = new FormData();
    list_polygons = []
    list_area_id = []
    for(var i=0;i<inputs.length;i++){
        list_polygons.push(inputs[i].value);
        list_area_id.push(area_id[i].value);
    }
    formData.append('polygons', JSON.stringify(list_polygons))
    formData.append('area_id', JSON.stringify(list_area_id))
    formData.append('cam_id', id)
    xhr = new XMLHttpRequest();

    xhr.open('post', '/save_polygons')
    xhr.send(formData);
}

function get_element_create_detector(form_){
    return  {'header': form_['rabbit_header'].value}
}

function get_element_create_classifaer(form_){
    return  {'header': form_['rabbit_header'].value,
            'type_classifaer': form_['type_classifaer'].value}
}

function button_click_add_cam(){
    let block = document.getElementById('hide_array2');
    console.log('Клик на кноку!');
    if (block.style.display =='block')
    {
        block.style.display='none';
        sessionStorage.setItem('block_add_cam', false);
    }
    else 
    {
        block.style.display ='block';
        sessionStorage.setItem('block_add_cam', true);
        block = document.getElementsByClassName('show_add_cam')[0];
        block.style.display = 'none';
    };
    return false;
}

function button_click_add_classifaer(){
    // let block = document.getElementById('id_add_classifaer');
    // if (block.style.display =='block')
    // {
    //     block.style.display='none';
    // }
    // else 
    // {
        let block = document.getElementById('id_add_classifaer');
        block.style.display ='block';
        block = document.getElementsByClassName('button_show_add_detector')[0];
        block.style.display = 'none';
    // };
    return false;
}

function button_click_add_detector(){
    let block = document.getElementById('id_add_detector');
    block.style.display ='block';
    block = document.getElementsByClassName('button_show_add_detector')[0];
    block.style.display = 'none';
    return false;
}

function button_click_video_mode(objButton){
    if (objButton.value=='load_video'){
        node_load_video = document.getElementById('load_video_setting');
        node_strim = document.getElementById('strim_setting');
        if(node_load_video != null){
            if(node_load_video.style.display=='none'){
                node_strim.style.display = 'none';
                node_load_video.style.display='block';
            }
        }
    }else{
        node_load_video = document.getElementById('load_video_setting');
        node_strim = document.getElementById('strim_setting');
        if(node_strim != null){
            if(node_strim.style.display=='none'){
                node_load_video.style.display = 'none';
                node_strim.style.display='block';
            }
        }
    }
    return false;
}

function button_click_show_extend_setting(){
    node_extend_setting = document.getElementById('extend_setting');
    if(node_extend_setting.style.display=='none')
    {node_extend_setting.style.display = 'block';}
    else {node_extend_setting.style.display = 'none';}
    return false;
}

// Выпадающее меню
/* Когда пользователь нажимает на кнопку, переключаться раскрывает содержимое */
function myFunction() {
    document.getElementById("myDropdown").classList.toggle("show");
  }
  // Закрыть раскрывающийся список, если пользователь щелкнет за его пределами.
  window.onclick = function(event) {
    if (!event.target.matches('.dropbtn')) {
      var dropdowns = document.getElementsByClassName("dropdown-content");
      var i;
      for (i = 0; i < dropdowns.length; i++) {
        var openDropdown = dropdowns[i];
        if (openDropdown.classList.contains('show')) {
          openDropdown.classList.remove('show');
        }
      }
    }
  }

//   setting 
function button_click_add_polygons_setting(button){
    
    if(button.name == 'add'){
        node = document.getElementsByClassName('list_polygons')[0];
        create_polygons_by_setting(node, [{'polygons':'', 'area_id': ''}])
    }
    else if(button.name == 'save'){
        form_ = document.forms['form_polygons'];
        list_polygons = form_.querySelectorAll('input[name="polygons"]');
        list_area_id = form_.querySelectorAll('input[name="area_id"]');
        
        formData = new FormData();
        var request = new XMLHttpRequest();
        request.open('POST', `/save_polygons_map`);
        list = []
        for(var i = 0; i < list_area_id.length; i++){
            ok = true;
            if(list_area_id[i].value == null || list_area_id[i].value == ""){
                list_area_id[i].style.borderColor = 'red';
                ok=false;
            }else{
                //list_area_id[i].style.borderColor = 'black';
                list_area_id[i].style.border = '1px solid black';
            }
            
            if(list_polygons[i].value == null || list_polygons[i].value == ""){
                list_polygons[i].style.borderColor = 'red';
                ok=false;
            }else{
                //list_polygons[i].style.borderColor = 'black';
                list_polygons[i].style.border = '1px solid black';
            }

            if(ok)
                list.push({'area_id':list_area_id[i].value, 'polygons':list_polygons[i].value});
        }

        formData.append('list_polygons', JSON.stringify(list));
        request.send(formData);

    }else{
        draw_polygon_setting();
    }
    return false;
}

function create_polygons_by_setting(node, list_polygons){
    id_elem = document.getElementsByClassName('polygons_item').length;
    for(var i = 0; i<list_polygons.length; i++){
        var elemDiv = document.createElement('div');
        elemDiv.className = 'polygons_item';
        elemDiv.setAttribute('name',"polygons_item_" + id_elem);
        elemDiv.id = "polygons_item_" + id_elem;
        
        var Div_ = document.createElement('div');
        var label_ = document.createElement('label');
        label_.innerText = 'Полигон';
        label_.setAttribute('for','polygons');
        
        var input_ = document.createElement('input');
        input_.setAttribute('class', 'polygons_coord');
        input_.setAttribute('type', 'text');
        input_.setAttribute('name', 'polygons');
        input_.value = list_polygons[i]['polygons'];
        input_.onchange = function () {  
            validation_polygons(this);
        };

        Div_.appendChild(label_);
        Div_.appendChild(input_);
        elemDiv.appendChild(Div_);

        Div_ = document.createElement('div');
        label_ = document.createElement('label');
        label_.innerText = 'Номер зоны';
        label_.setAttribute('for','polygons');

        input_ = document.createElement('input');
        input_.setAttribute('type', 'number');
        input_.setAttribute('class', 'area_id');
        input_.setAttribute('name', 'area_id');
        input_.value = list_polygons[i]['area_id'];
        
        // input_.onchange = function () {  
        //     validation_polygons(this);
        // };

        Div_.appendChild(label_);
        Div_.appendChild(input_);
        elemDiv.appendChild(Div_);

        Div_ = document.createElement('div');
        Div_.innerHTML = `<span class="closebtn" id="${id_elem}" \
                                onclick="span_click_closebtn_setting(this)">&times;</span> `
        
        elemDiv.appendChild(Div_);

        node.appendChild(elemDiv);
        id_elem+=1;
    }
}
function span_click_closebtn_setting(button){
    id = button.id
    formData = new FormData();
    var request = new XMLHttpRequest();
    request.open('POST', `/delete_polygons`);
    area_id = document.getElementById('polygons_item_'+ id);
    area_id = area_id.querySelector('input[name=area_id]').value
    
    if(area_id!=null){
        console.log(area_id);
        formData.append('area_id', area_id);
        request.send(formData);

    }

    node = document.getElementsByClassName('list_polygons')[0];
    node.removeChild(node.querySelector('#polygons_item_'+id));
}

function draw_polygon_setting(){

    node_map = document.getElementsByClassName('svg_map')[0];
    list_path = node_map.querySelectorAll('path[class="part"]');

    mas_len = list_path.length;
    for(var i = 0 ; i< mas_len;i++){
        node_map.removeChild(list_path[i]);
    }

    form_ = document.forms['form_polygons'];
    list_polygons = form_.querySelectorAll('input[name="polygons"]');

    for(var i = 0; i < list_polygons.length; i++){
            elem = document.createElementNS('http://www.w3.org/2000/svg', 'path');
            elem.setAttribute('d',list_polygons[i].value);
            elem.setAttribute('style', 'opacity: 0.55; fill: green;');
            elem.setAttribute('class', 'part');
            node_map.appendChild(elem);
    }

}
