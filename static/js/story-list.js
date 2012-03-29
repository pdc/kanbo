// Make the stories be sortable.

$(function () {
    $('.story-bin').sortable({
        connectWith: '.story-bin',
        update: function (event, ui) {
            var eltIDs = $(this).sortable('toArray');
            var storyIDs = [];
            for (var i = 0; i < eltIDs.length; ++i) {
                storyIDs.push(eltIDs[i].replace(/^story-/, ''));
            }
            var form$ = $(this).parent().find('form');
            $('input[name=order]', form$).val(storyIDs.join(' '));
        }
    })
    .disableSelection();
});