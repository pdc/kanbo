// Make the stories be sortable.

$(function () {
    $('.story-bin').sortable({
        connectWith: '.story-bin',
        update: function (event, ui) {
            var droppedID = ui.item.attr('id').replace(/^story-/, '');
            var eltIDs = $(this).sortable('toArray');
            var storyIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                storyIDs.push(eltIDs[i].replace(/^story-/, ''));
            }
            var droppedIndex = storyIDs.indexOf(droppedID);
            if (droppedIndex >= 0) {
                var succID = (droppedIndex + 1 < storyIDs.length ? storyIDs[droppedIndex + 1] : '-');
                var abbreviatedIDs = [droppedID, succID];

                var form$ = $(this).parent().find('form');
                var ajaxEnabled = $('#ajaxEnabled:checked').length;
                if (ajaxEnabled) {
                    var url = $(this).attr('data-ajax-url');
                    var data = {}
                    var es = $('input[type=hidden]', form$).get();
                    for (var i = 0; i < es.length; ++i) {
                        data[es[i].name] = es[i].value;
                    }
                    data[ 'order'] =  abbreviatedIDs.join(' ');
                    data['dropped'] = droppedID;
                    $.ajax(url, {
                        type: 'POST',
                        dataType: 'json',
                        data: data,
                        success: function (data, textStatus, jqXHR) {
                            console.log(data);
                            console.log(textStatus);
                        }
                    });
                } else {
                    $('input[name=order]', form$).val(abbreviatedIDs.join(' '));
                    $('input[name=dropped]', form$).val(droppedID);
                }
            }
        }
    })
    .disableSelection();
});