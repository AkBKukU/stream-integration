function adjust(color, amount) {
	    return '#' + color.replace(/^#/, '').replace(/../g, color => ('0'+Math.min(255, Math.max(0, parseInt(color, 16) + amount)).toString(16)).substr(-2));
}
// Chat Message Handling
function chat_read(chat_data)
{
    if(chat_data.length ==0)
    {
      return
    }

    chat_list = document.getElementById("chat-list");
    chat_list.textContent = '';

    chat_data.forEach((c) => {
        li = document.createElement("li");
        if ('icons' in c && c["icons"] != null) c["icons"].forEach((i) => {
            var img = document.createElement("img");
            img.src=i;
            img.classList.add("icon");
            li.appendChild(img);
        });

        var name = document.createElement("span");
        name.innerHTML = c['from'];
        name.style.color = adjust(c['color'],30);
        name.classList.add("name");
        li.appendChild(name)

        var text = document.createElement("span");
        text.innerHTML = ": " + c['text'];
        text.classList.add("text");
        li.appendChild(text)

        chat_list.appendChild(li)
    });

}

// Subs Message Handling
sub_last_timestamp=""
function subs_read(subs_data)
{
    if(subs_data.length ==0)
    {
      return
    }

    most_recent = subs_data[subs_data.length-1]

    if ( most_recent['timestamp'] == sub_last_timestamp ) return
    sub_last_timestamp = most_recent['timestamp']

    message_box = document.getElementById("message-box");
    message_box.textContent = most_recent['text'];


    message_box.classList.add('fade-in');
    message_box.classList.remove('fade-out');
    setTimeout(subs_fade_out,10000)
}



// Poll Handling
function poll_read(poll_data)
{
    if(poll_data.length ==0)
    {
      return
    }

    if (!poll_data.valid)
    {
            poll_box = document.getElementById("poll-box");
            poll_box.classList.add('fade-out');
            poll_box.classList.remove('fade-in');
	    return
    }

    poll_list = document.getElementById("poll-list");
    poll_list.textContent = '';

    poll_title = document.getElementById("poll-title");
    if (poll_data.remaining > 1)
    {
       poll_title.textContent = poll_data.remaining-1 +"s: "+ poll_data.title;
    }else{
       poll_title.textContent = "Done: "+ poll_data.title;
    }
    total = 0
    win_key = ""
    win_value = 0
    for (const [key, value] of Object.entries(poll_data.data))
    {
      total += value;
      if (value > win_value)
      {
        win_key = key;
        win_value = value;
      }
    }

    for (const [key, value] of Object.entries(poll_data.data)) {

        li = document.createElement("li");

        div = document.createElement("div");
        div.style.width = ((value/total)*100)+"%"
        if ( poll_data.remaining <= 1 && win_key == key)
        {
          div.style.backgroundColor = "rgba(255,32, 32, 0.45)";
        }
        div.classList.add("poll-bar");

        var text = document.createElement("span");
        text.innerHTML = key
        text.classList.add("poll-text");
        li.appendChild(text)

        var count = document.createElement("span");
        count.innerHTML = value
        count.classList.add("poll-count");
        li.appendChild(count)

        li.appendChild(div)
        poll_list.appendChild(li)

    };
    poll_box = document.getElementById("poll-box");
    poll_box.classList.add('fade-in');
    poll_box.classList.remove('fade-out');
}


function subs_fade_out()
{
    message_box = document.getElementById("message-box");
    message_box.classList.add('fade-out');
    message_box.classList.remove('fade-in');
}

// Chat Data Loop
function chat_fetch()
{
  fetch('chat.json')
    .then((response) => response.json())
    .then((data) => chat_read(data));

  setTimeout(chat_fetch,1000)
}

// Subs Data Loop
function subs_fetch()
{
  fetch('subs.json')
    .then((response) => response.json())
    .then((data) => subs_read(data));

  setTimeout(subs_fetch,1000)
}

// Poll Data Loop
function poll_fetch()
{
  fetch('poll.json')
    .then((response) => response.json())
    .then((data) => poll_read(data));

  setTimeout(poll_fetch,1000)
}



// Final Init
setTimeout(chat_fetch,1000)
setTimeout(subs_fetch,1000)
setTimeout(poll_fetch,1000)
document.getElementById("message-box").classList.add('fade-out');
document.getElementById("poll-box").classList.add('fade-out');
