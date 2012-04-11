// Make the stories be sortable.

var StoryGrid = (function ($) {
    // Poll for updates from the server.
    var pendingPoll;

    function pollForUpdates(url) {
        // XXX som,ethjign to prevent overlapping polling.

        $('body').addClass('polling');
        $.ajax(url, {
            type: 'GET',
            dataType: 'json',
            success: function (data, textStatus, jqXHR) {
                if (data.ready && data.events) {
                    for (var i = 0; i < data.events.length; ++i) {
                        var event = data.events[i];
                        if (event.type == 'rearrange' && event.dropped && event.order) {
                            var succID = event.order[1];
                            // XXX this will be null iff dropped item goes at the end of the list.
                            $('#story-' + event.dropped).insertBefore('#story-' + succID);
                        }
                        console.log(event);
                    }
                }

                if (data.next) {
                    pendingPoll = window.setTimeout(
                        function () {
                            pendingPoll = null;
                            pollForUpdates(data.next);
                        },
                        data.pleaseWait || 100);
                }
            },
            complete: function (jqXHT, textStatus) {
                $('body').removeClass('polling');
            }
        });
    }

    return {
        pollForUpdates: pollForUpdates
    };
})(jQuery);

$(function () {
    var ajaxEnabled = true;

    // Make the story bins be sortable with drag-and-drop.
    $('.story-bin').sortable({
        connectWith: '.story-bin',
        update: function (event, ui) {
            // Report the change to the server.
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
                if (ajaxEnabled) {
                    var url = $(this).attr('data-ajax-url');
                    var data = {}
                    var es = $('input[type=hidden]', form$).get();
                    for (var i = 0; i < es.length; ++i) {
                        data[es[i].name] = es[i].value;
                    }
                    data[ 'order'] =  abbreviatedIDs.join(' ');
                    data['dropped'] = droppedID;
                    ui.item.addClass('ajax-loading');
                    $.ajax(url, {
                        type: 'POST',
                        dataType: 'json',
                        data: data,
                        success: function (data, textStatus, jqXHR) {
                            //console.log(data);
                            //console.log(textStatus);
                        },
                        complete: function (jqXHR, textStatus) {
                            ui.item.removeClass('ajax-loading');
                        }
                    });
                } else {
                    $('input[name=order]', form$).val(abbreviatedIDs.join(' '));
                    $('input[name=dropped]', form$).val(droppedID);
                }
            }
        }
    })
    .disableSelection()
    .parent().find('form').hide();
});